name: Run Python Script

on:
  push:
    branches:
      - main  # Main branch-a push edildikdə işə düşəcək
  schedule:
    - cron: "0 * * * *"  # Hər saat başı çalışsın

jobs:
  run:
    runs-on: ubuntu-latest  # GitHub Actions üçün Ubuntu istifadə edirik

    steps:
      # Kodunuzu GitHub reposundan çəkin
      - name: Checkout repository
        uses: actions/checkout@v2

      # Python mühitini qurun
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.x  # Python 3.x versiyasını istifadə edin

      # Lazım olan asılılıqları quraşdırın
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt  # requirements.txt faylını istifadə edirik

      # Google Chrome-u quraşdırın
      - name: Install Google Chrome
        run: |
          sudo apt-get update -y
          sudo apt-get install -y google-chrome-stable  # Chrome yükləyirik

      # ChromeDriver-ı quraşdırın
      - name: Install ChromeDriver
        run: |
          CHROME_VERSION=$(google-chrome-stable --version | awk '{print $3}' | sed 's/\..*//')  # Chrome versiyasını alırıq
          wget https://chromedriver.storage.googleapis.com/113.0.5672.63/chromedriver_linux64.zip  # Uyğun ChromeDriver versiyasını yükləyirik
          unzip chromedriver_linux64.zip
          sudo mv chromedriver /usr/local/bin/  # ChromeDriver-ı sistemə yerləşdiririk
          sudo chmod +x /usr/local/bin/chromedriver

      # Python skriptini işə salın
      - name: Run script
        run: python get_m3u8_link.py  # Skriptin adı
