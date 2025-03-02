name: Set Up Chromedriver

on:
  push:
    branches:
      - main

jobs:
  setup:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8

    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y wget unzip

    - name: Run Chromedriver Setup Script
      run: |
        chmod +x ./install_chromedriver.sh
        ./install_chromedriver.sh
