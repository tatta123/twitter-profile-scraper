import csv
import atexit
import signal
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time

def extract_number_from_string(s):
    match = re.search(r'\d[\d,]*(?=\D|$)', s.replace(',', ''))
    return int(match.group(0).replace(',', '')) if match else 0

def save_csv_on_exit(data_list):
    csv_file = "kat2.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["User", "Tweet Text", "Timestamp", "Replies", "Retweets", "Quotes", "Hearts (Likes)", "Tweet URL"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_list)

def scrape_tweets_with_load_more(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")

    data_list = []
    tweet_count = 0

    with webdriver.Chrome(options=options) as driver:
        driver.get(url)
        time.sleep(0.5)  # Give the initial page time to load

        # Register the save_csv_on_exit function to be called when the script exits
        atexit.register(save_csv_on_exit, data_list)

        while True:
            page_source = driver.page_source

            soup = BeautifulSoup(page_source, "html.parser")
            tweets = soup.find_all("div", class_="timeline-item")

            # Check for "No more items" or "Load newest" messages
            no_more_items = soup.find("div", text="No more items")
            load_newest = soup.find("div", text="Load newest")

            if no_more_items:
                print("No more tweets to load. Reloading the page...")
                driver.refresh()
                time.sleep(0.25)  # Reduce the delay for refreshing
                continue

            if not tweets:
                print("No tweets found on the page. Reloading the page...")
                driver.refresh()
                time.sleep(0.25)  # Reduce the delay for refreshing
                continue

            for tweet in tweets:
                tweet_content = tweet.find("div", class_="tweet-content")
                tweet_text = tweet_content.text.strip() if tweet_content else "Tweet content not found"

                user_tag = tweet.find("div", class_="fullname-and-username")
                user = user_tag.a["title"] if user_tag else "User mention only"

                timestamp_tag = tweet.find("span", class_="tweet-date")
                try:
                    timestamp = timestamp_tag.a['title']
                except (AttributeError, TypeError):
                    timestamp = "Timestamp not found"

                try:
                    comment_count_element = tweet.find("span", class_="icon-comment")
                    comment_count = extract_number_from_string(comment_count_element.find_next(string=True).strip()) if comment_count_element else 0
                except Exception as e:
                    print("Error while extracting comment count:", e)
                    comment_count = 0

                try:
                    retweet_count_element = tweet.find("span", class_="icon-retweet")
                    retweet_count = extract_number_from_string(retweet_count_element.find_next(string=True).strip()) if retweet_count_element else 0
                except Exception as e:
                    print("Error while extracting retweet count:", e)
                    retweet_count = 0

                try:
                    quote_count_element = tweet.find("span", class_="icon-quote")
                    quote_count = extract_number_from_string(quote_count_element.find_next(string=True).strip()) if quote_count_element else 0
                except Exception as e:
                    print("Error while extracting quote count:", e)
                    quote_count = 0

                try:
                    heart_count_element = tweet.find("span", class_="icon-heart")
                    heart_count = extract_number_from_string(heart_count_element.find_next(string=True).strip()) if heart_count_element else 0
                except Exception as e:
                    print("Error while extracting heart count:", e)
                    heart_count = 0

                try:
                    tweet_link = tweet.find("a", class_="tweet-link")["href"]
                except (TypeError, KeyError):
                    tweet_link = "Tweet link not found"

                tweet_data = {
                    "User": user,
                    "Tweet Text": tweet_text,
                    "Timestamp": timestamp,
                    "Replies": comment_count,
                    "Retweets": retweet_count,
                    "Quotes": quote_count,
                    "Hearts (Likes)": heart_count,
                    "Tweet URL": tweet_link,
                }

                data_list.append(tweet_data)
                tweet_count += 1

                # Print the count every 20 seconds
                if tweet_count % 20 == 0:
                    print(f"Number of tweets scraped: {tweet_count}")

            # Find the "Load more" link and check if it's visible
            load_more_link = soup.find("a", text="Load more")
            if load_more_link:
                cursor_match = re.search(r'cursor=(\d+)', load_more_link['href'])
                if cursor_match:
                    cursor_value = cursor_match.group(1)
                    load_more_url = f"https://nitter.poast.org/search?f=tweets&q=from:katgraham&since=&until=2016-01-01&near=&cursor={cursor_value}"
                    driver.get(load_more_url)
                    time.sleep(0.25)  # Reduce the delay for loading more tweets
                else:
                    print("Error: Could not extract cursor value from the 'Load more' link.")
                    break
            else:
                print("No more tweets to load. Exiting the scraping process...")
                break

if __name__ == "__main__":
    url = "https://nitter.poast.org/search?f=tweets&q=from:katgraham&since=&until=2016-01-01&near="
    scrape_tweets_with_load_more(url)
