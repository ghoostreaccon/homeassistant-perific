# Perific Energy Meter for Home Assistant

A custom Home Assistant integration for Perific/Enegic energy meters.

It exposes power, energy, voltage, and current sensors and supports the Home Assistant Energy dashboard.

> This project started as an AI-assisted learning experiment. Contributions and fixes are welcome.

## Features

- Total and per-phase power
- Imported, exported, and net energy
- Per-phase voltage and current
- Home Assistant Energy dashboard support
- HTTP polling of the Perific/Enegic API

## Installation

### HACS

1. Add this repository to HACS as a custom repository.
2. Install **Perific Energy Meter**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**.
5. Search for **Perific Energy Meter**.

### Manual

Copy:

```text
custom_components/perific
```

to your Home Assistant `custom_components` directory, restart Home Assistant, then add the integration from **Settings → Devices & services**.

## Configuration

You need your Perific account email and API token.

To find the token:

1. Sign in to the Perific web app.
2. Open your browser developer tools.
3. Open the **Network** tab.
4. Find a request to `api.enegic.com`.
5. Copy the value of the `X-Authorization` header.

## Sensors

For each meter, the integration creates sensors for:

- Total power and L1/L2/L3 power
- Imported energy
- Exported energy
- Net energy
- L1/L2/L3 voltage
- L1/L2/L3 current

Energy entities use Home Assistant-compatible energy metadata so they can be used for long-term statistics and the Energy dashboard.

## Home Assistant Energy dashboard

Go to:

**Settings → Dashboards → Energy**

Use:

- **Energy Imported** for grid consumption
- **Energy Exported** for return to grid

Do not use **Energy Net** as the grid consumption or return-to-grid entity.

If an energy sensor does not appear in the selector, check it in **Developer Tools → States**. Imported/exported sensors should have:

```text
device_class: energy
state_class: total_increasing
unit_of_measurement: kWh
```

Home Assistant may also need some statistics history before a newly added entity appears in the Energy dashboard.

See Home Assistant's Energy FAQ for troubleshooting:
https://www.home-assistant.io/docs/energy/faq/#troubleshooting-missing-entities

## Troubleshooting

If sensors do not update:

- Check the Home Assistant logs.
- Verify the email and API token.
- Confirm the Perific device is reporting data.
- Restart Home Assistant after updating the integration.

## API details

More API information is available in [PERIFIC_API_DOCUMENTATION.md](PERIFIC_API_DOCUMENTATION.md).

## License

MIT
