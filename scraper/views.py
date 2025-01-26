from django.shortcuts import render
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
from django.http import JsonResponse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Prepare the browser for Selenium
def prepare_browser():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Login to Instagram (called before scraping if needed)
def login_to_instagram(chrome, username, password):
    chrome.get("https://www.instagram.com/accounts/login/")
    WebDriverWait(chrome, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    username_input = chrome.find_element(By.NAME, "username")
    password_input = chrome.find_element(By.NAME, "password")

    username_input.send_keys(username)
    password_input.send_keys(password)
    chrome.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    # Wait for the page to load after login
    WebDriverWait(chrome, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="presentation"]'))
    )

# Scrape a user's profile
def scrape(username):
    url = f"https://www.instagram.com/{username}/"
    chrome = prepare_browser()
    chrome.get(url)

    # Wait for specific meta tags to be present
    WebDriverWait(chrome, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[property="og:title"]'))
    )

    html = chrome.page_source
    soup = BeautifulSoup(html, "html.parser")
    user_data = {}

    try:
        profile_name_tag = soup.find("meta", property="og:title")
        bio_tag = soup.find("meta", property="og:description")
        
        if not profile_name_tag or not bio_tag:
            print(f"Profile name or bio tag not found for {username}. HTML Source: {html}")
            return user_data

        profile_name = profile_name_tag.get("content", "")
        bio = bio_tag.get("content", "")
        followers = bio.split(",")[0].split(" ")[0]

        user_data = {
            "profile_name": profile_name,
            "followers": followers,
            "bio": bio,
        }
    except Exception as e:
        print(f"Error while scraping {username}: {e}")
    finally:
        chrome.quit()

    return user_data


# Django view for handling requests
def index(request):
    scraped_data = {}
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        if username:
            scraped_data = scrape(username)
            if not scraped_data:
                error = f"Could not retrieve data for username: {username}"
        else:
            error = "No username provided."

    return render(request, "scraper/index.html", {"data": scraped_data, "error": error})


# Convert scrape function into a view that returns JSON
def scrape_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        if username:
            scraped_data = scrape(username)
            if scraped_data:
                return JsonResponse({"success": True, "data": scraped_data})
            else:
                return JsonResponse({"success": False, "error": "Failed to scrape data"})
        else:
            return JsonResponse({"success": False, "error": "No username provided"})
    return JsonResponse({"success": False, "error": "Invalid request method"})
