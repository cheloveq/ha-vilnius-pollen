<p align="center"><img src="logo.png" width="180" alt="Vilnius Pollen logo"></p>

<h1 align="center">Vilnius Pollen</h1>

<p align="center">Authoritative Vilnius pollen measurements for Home Assistant.</p>

`Vilnius Pollen` is a lightweight Home Assistant custom integration for the public [Vilnius OpenCity Bioaerozoliai](https://opencity.idvilnius.lt/atviras/rest/services/Aplinka/Bioaerozoliai/MapServer) service. It reports real measurements from Vilnius's dedicated pollen/bioaerosol monitoring site—no account, API key, coordinates, or forecast model required.

It intentionally complements, rather than combines with, [ha-miesto-plauciai](https://github.com/untitledlt/ha-miesto-plauciai): that project covers conventional outdoor air pollution; this one covers pollen/bioaerosols. Its integration structure and visual identity were inspired by `ha-miesto-plauciai`; the implementation, pollen data model, history access, and branding assets are maintained separately.

## Features

- One-click setup: **Settings → Devices & services → Add integration → Vilnius Pollen**.
- Hourly measurements for alder, birch, grass, hazel, mugwort, and ragweed pollen.
- A separate source-derived **symptom-risk** label—Low, Medium, High, or Very high—for each taxon.
- A source timestamp, five-minute coordinated polling, and availability protection when a measurement is more than three hours old.
- Recorder history and long-term statistics from installation onward.
- `vilnius_pollen.query_history`: a bounded, read-only action for querying pre-existing official history without importing it into Home Assistant Recorder.
- English and Lithuanian translations, diagnostics, and local Home Assistant brand assets.

## Install with HACS

1. In HACS, open **Integrations** and choose the three-dot menu → **Custom repositories**.
2. Add `https://github.com/cheloveq/ha-vilnius-pollen` as an **Integration**.
3. Search for **Vilnius Pollen**, install it, and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**, select **Vilnius Pollen**, then finish the one-click flow.

## Manual installation

Copy `custom_components/vilnius_pollen` into your Home Assistant `config/custom_components` directory, restart Home Assistant, then add **Vilnius Pollen** through the UI.

## Entities and data semantics

Each taxon has two entities:

- A numeric pollen concentration in `vnt./m³`, with Home Assistant's `measurement` state class for history and statistics.
- A separately named source-derived risk enum. It is an attributed presentation of Miesto Plaučiai's published bands, not medical advice and not a replacement for the measured concentration.

Concentrations are rounded to one decimal place for useful display and statistics. The exact upstream float remains available as the entity's `source_value` attribute; risk banding uses that unrounded source value. A source null remains `unknown`.

The layer-0 `Pollen` “total” field is intentionally excluded. It stopped receiving values in December 2021 and is not displayed by Miesto Plaučiai.

## Official source history

Layer 0 is the hourly source series. Its frontend uses UTC date bounds and pagination. Query a bounded period from **Developer tools → Actions**:

```yaml
action: vilnius_pollen.query_history
data:
  start: "2026-09-08T00:00:00+00:00"
  end: "2026-09-09T00:00:00+00:00"
  limit: 500
```

The action returns up to 2,000 ordered source records. It does not backfill Home Assistant Recorder. Layer 1 is a different daily dataset with undocumented aggregation semantics and is deliberately not exposed as V1 sensor entities.

## Migrating from Vilnius Allergens

`v0.2.0` renames the integration domain from `vilnius_allergens` to `vilnius_pollen` to describe the source accurately. Home Assistant treats this as a new integration: remove the old **Vilnius Allergens** entry, restart after removing its custom-component directory, install **Vilnius Pollen**, then add the new one-click entry. Existing Recorder history is retained under the former `vilnius_allergens` entity IDs; the new `vilnius_pollen` entities begin their own history.

## Privacy, limitations, and attribution

The integration makes an unauthenticated HTTPS request to the public Vilnius OpenCity service every five minutes. It sends no account data, location, or credentials; source history is requested only when the explicit action runs.

The source presents hourly rows while its service metadata also refers to 12-hour accumulation. This integration reports the source measurements without asserting an unresolved aggregation methodology. It does not provide medical guidance.

Data source: [Vilnius OpenCity Bioaerozoliai](https://opencity.idvilnius.lt/atviras/rest/services/Aplinka/Bioaerozoliai/MapServer). The project was inspired by [untitledlt/ha-miesto-plauciai](https://github.com/untitledlt/ha-miesto-plauciai), which remains the appropriate companion integration for Vilnius air pollution.

## Development

```bash
python -m pytest -q
```

The project is licensed under the [MIT License](LICENSE).
