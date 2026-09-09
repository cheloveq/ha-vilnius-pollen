# Vilnius Allergens

Home Assistant integration for authoritative, Vilnius-wide pollen measurements from the public [Vilnius OpenCity Bioaerozoliai](https://opencity.idvilnius.lt/atviras/rest/services/Aplinka/Bioaerozoliai/MapServer) service.

It is deliberately separate from air-pollution integrations: these are biological-allergen measurements from one dedicated site, not conventional atmospheric pollutants or forecasts.

## What it provides

- one-click setup: **Settings → Devices & services → Add integration → Vilnius Allergens**;
- hourly raw concentrations for alder, ragweed, mugwort, birch, hazel, and grass;
- a source timestamp and freshness-based availability (measurements older than three hours become unavailable);
- Home Assistant history and long-term statistics from installation onward;
- a read-only `vilnius_allergens.query_history` action for bounded, pre-existing official history. It does **not** import historical source records into Recorder.

All measurements use the source/frontend unit `vnt./m³` (pollen units per cubic metre). A null source value remains `unknown`; no thresholds or medical advice are invented. The source's legacy `Pollen` field is deliberately excluded: it stopped receiving values after December 2021 and is not used by Miesto Plaučiai.

## Historical source access

Layer 0 is the hourly source series. The upstream frontend queries it directly with UTC date bounds and pagination. Use the action in Developer Tools when external history is needed:

```yaml
action: vilnius_allergens.query_history
data:
  start: "2026-09-08T00:00:00+00:00"
  end: "2026-09-09T00:00:00+00:00"
  limit: 500
```

The action returns at most 2,000 records in ascending timestamp order. Layer 1 is a different daily source series with undocumented aggregation semantics; it is intentionally not exposed as V1 sensors.

## Installation

Until a GitHub/HACS release exists, copy `custom_components/vilnius_allergens` into your Home Assistant `config/custom_components` directory, restart Home Assistant, then add the integration through the UI. No API key, coordinates, or account is required.

## Data and privacy

The integration makes an unauthenticated HTTPS request to the public Vilnius OpenCity layer every five minutes. It sends no location, account data, or credentials. Source history is queried only when the explicit action is called.

## Status and limitations

The upstream source presents hourly rows, while its service metadata also mentions 12-hour accumulation. This integration reports source values exactly as received and makes no claim about that unresolved aggregation methodology. Total pollen is currently often null upstream.
