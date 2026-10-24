<?php

declare(strict_types=1);

const DEFAULT_SOURCE_URL = 'https://www.mkejazz.live';
const DEFAULT_EVENT_TIMEZONE = 'America/Chicago';
const JSON_LD_ELEMENT_ID = 'event-schema-ld';

final class EventIcsException extends RuntimeException
{
}

function fetchPage(string $url): string
{
    $parts = parse_url($url);
    if (!$parts || !in_array(strtolower($parts['scheme'] ?? ''), ['http', 'https'], true)) {
        throw new EventIcsException('Enter a valid HTTP or HTTPS URL.');
    }

    $curl = curl_init($url);
    if ($curl === false) {
        throw new EventIcsException('Unable to initialize the HTTP client.');
    }

    curl_setopt_array($curl, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 5,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_USERAGENT => 'Event-ICS-Exporter/1.0',
        CURLOPT_HTTPHEADER => ['Accept: text/html,application/xhtml+xml'],
    ]);

    $html = curl_exec($curl);
    $status = (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    $error = curl_error($curl);

    if ($html === false) {
        throw new EventIcsException('The source page could not be fetched: ' . $error);
    }
    if ($status >= 400) {
        throw new EventIcsException("The source page returned HTTP {$status}.");
    }

    return $html;
}

function extractJsonLd(string $html): mixed
{
    $document = new DOMDocument();
    $previous = libxml_use_internal_errors(true);
    $loaded = $document->loadHTML('<?xml encoding="UTF-8">' . $html, LIBXML_NONET | LIBXML_NOERROR | LIBXML_NOWARNING);
    libxml_clear_errors();
    libxml_use_internal_errors($previous);

    if (!$loaded) {
        throw new EventIcsException('The source page did not contain readable HTML.');
    }

    $nodes = (new DOMXPath($document))->query('//*[@id="' . JSON_LD_ELEMENT_ID . '"]');
    if ($nodes === false || $nodes->length === 0) {
        throw new EventIcsException('No element with id "' . JSON_LD_ELEMENT_ID . '" was found.');
    }

    $json = trim($nodes->item(0)->textContent);
    $data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);

    return $data;
}

function findEvents(mixed $data): array
{
    if (!is_array($data)) {
        return [];
    }

    $events = [];
    $type = $data['@type'] ?? null;
    $types = is_array($type) ? $type : [$type];
    if (in_array('Event', $types, true) || in_array('MusicEvent', $types, true)) {
        $events[] = $data;
    }

    foreach ($data as $value) {
        if (is_array($value)) {
            $events = [...$events, ...findEvents($value)];
        }
    }

    return $events;
}

function valueAsString(mixed $value): ?string
{
    if (is_string($value) || is_numeric($value)) {
        return trim((string) $value);
    }
    return null;
}

function eventLocation(mixed $location): ?string
{
    if (is_string($location)) {
        return trim($location);
    }
    if (!is_array($location)) {
        return null;
    }

    $name = valueAsString($location['name'] ?? null);
    $address = $location['address'] ?? null;
    if (is_array($address)) {
        $addressParts = array_filter([
            valueAsString($address['streetAddress'] ?? null),
            valueAsString($address['addressLocality'] ?? null),
            valueAsString($address['addressRegion'] ?? null),
            valueAsString($address['postalCode'] ?? null),
        ]);
        $address = implode(', ', $addressParts);
    } else {
        $address = valueAsString($address);
    }

    return implode(', ', array_filter([$name, $address]));
}

function parseEventDate(mixed $value, DateTimeZone $timezone): ?DateTimeImmutable
{
    $date = valueAsString($value);
    if ($date === null || $date === '') {
        return null;
    }

    try {
        return new DateTimeImmutable($date, $timezone);
    } catch (Exception) {
        return null;
    }
}

function icsEscape(string $value): string
{
    return str_replace(['\\', ';', ',', "\r\n", "\r", "\n"], ['\\\\', '\\;', '\\,', '\\n', '\\n', '\\n'], trim($value));
}

function foldIcsLine(string $line): string
{
    $result = '';
    while (strlen($line) > 75) {
        $result .= substr($line, 0, 75) . "\r\n ";
        $line = substr($line, 75);
    }
    return $result . $line;
}

function formatIcsDate(DateTimeImmutable $date, bool $dateOnly): string
{
    return $dateOnly ? $date->format('Ymd') : $date->setTimezone(new DateTimeZone('UTC'))->format('Ymd\THis\Z');
}

function makeIcs(array $events, string $sourceUrl): string
{
    $timezone = new DateTimeZone(DEFAULT_EVENT_TIMEZONE);
    $lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Event ICS Exporter//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'X-WR-CALNAME:MKE Jazz Live Events',
    ];

    foreach ($events as $index => $event) {
        $start = parseEventDate($event['startDate'] ?? null, $timezone);
        if ($start === null) {
            continue;
        }
        $end = parseEventDate($event['endDate'] ?? null, $timezone);
        $dateOnly = !str_contains(valueAsString($event['startDate'] ?? '') ?? '', 'T');
        $uidSource = valueAsString($event['url'] ?? null) ?: $sourceUrl;
        $uid = hash('sha256', $uidSource . '|' . $start->format(DateTimeInterface::ATOM) . '|' . $index) . '@event-ics-exporter';

        $lines[] = 'BEGIN:VEVENT';
        $lines[] = 'UID:' . $uid;
        $lines[] = 'DTSTAMP:' . gmdate('Ymd\THis\Z');
        $lines[] = 'DTSTART' . ($dateOnly ? ';VALUE=DATE' : '') . ':' . formatIcsDate($start, $dateOnly);
        if ($end !== null) {
            $lines[] = 'DTEND' . ($dateOnly ? ';VALUE=DATE' : '') . ':' . formatIcsDate($end, $dateOnly);
        }
        $lines[] = 'SUMMARY:' . icsEscape(valueAsString($event['name'] ?? null) ?: 'Untitled event');

        foreach ([
            'description' => 'DESCRIPTION',
            'url' => 'URL',
        ] as $jsonKey => $icsKey) {
            $value = valueAsString($event[$jsonKey] ?? null);
            if ($value !== null && $value !== '') {
                $lines[] = $icsKey . ':' . icsEscape($value);
            }
        }

        $location = eventLocation($event['location'] ?? null);
        if ($location !== null && $location !== '') {
            $lines[] = 'LOCATION:' . icsEscape($location);
        }
        $lines[] = 'END:VEVENT';
    }

    $lines[] = 'END:VCALENDAR';
    return implode("\r\n", array_map('foldIcsLine', $lines)) . "\r\n";
}

try {
    $events = findEvents(extractJsonLd(fetchPage(DEFAULT_SOURCE_URL)));
    if ($events === []) {
        throw new EventIcsException('The JSON-LD element did not contain any Event or MusicEvent entries.');
    }

    header('Content-Type: text/calendar; charset=utf-8');
    header('Cache-Control: no-cache, must-revalidate');
    header('X-PUBLISHED-TTL: PT1H');
    echo makeIcs($events, DEFAULT_SOURCE_URL);
} catch (JsonException $exception) {
    http_response_code(502);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'The JSON-LD data is invalid: ' . $exception->getMessage();
} catch (EventIcsException $exception) {
    http_response_code(502);
    header('Content-Type: text/plain; charset=utf-8');
    echo $exception->getMessage();
} catch (Throwable $exception) {
    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Unexpected error: ' . $exception->getMessage();
}