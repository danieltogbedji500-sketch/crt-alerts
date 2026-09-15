```yaml
name: Prop-Firm Giveaway Detector

on:
  workflow_dispatch:

  schedule:
    # Every 3 hours
    - cron: "0 */3 * * *"

jobs:
  detect-giveaways:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run giveaway detector
        env:
          APIFY_API_TOKEN: ${{ secrets.APIFY_API_TOKEN }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
        run: |
          python detector.py
```
