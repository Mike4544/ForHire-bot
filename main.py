import traceback

from selenium import webdriver
# Import webdriverwait
from selenium.webdriver.support.ui import WebDriverWait
# Import expected_conditions
from selenium.webdriver.support import expected_conditions as EC

import io
import time
from bs4 import BeautifulSoup
import telebot
import re
from selenium.webdriver.common.by import By

from gpt4all import GPT4All

from threading import Thread

import requests

__LOGIN_NAME__ = "Prudent_Mongoose_123"
__LOGIN_PASS__ = "ENGaming4Life"


def create_bot():
    print("Creating bot...")

    __BOT_TOKEN__ = "6231823071:AAGw0hv5rwtVZXzi9z4ESyfhL2hjUcKhabg"
    bot = telebot.TeleBot(__BOT_TOKEN__)

    return bot


def send_bot_message(bot, message):
    bot.send_message(5625615047, message, parse_mode="MarkdownV2")


def reddit_delete_local_storage_and_cookies(driver):
    print("Deleting local storage and cookies...")

    # Delete local storage
    driver.execute_script("window.localStorage.clear();")

    # Delete cookies
    driver.delete_all_cookies()


def reddit_login(driver):
    # Open the login page
    driver.get("https://www.reddit.com/login/")
    time.sleep(1)

    # Find the email and password fields
    email_field = driver.find_element(By.ID, "loginUsername")
    password_field = driver.find_element(By.ID, "loginPassword")

    # Send the email and password
    email_field.send_keys(__LOGIN_NAME__)
    password_field.send_keys(__LOGIN_PASS__)

    # Find the login button
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")

    login_button.click()


def reddit_send_message_to_user(driver, user, subject, message):

    print(f"Sending message to {user}...")
    url = f"https://www.reddit.com/message/compose/?to={user}&subject={subject}&message={message}"
    driver.get(url)

    # driver wait for 1 seconds to load the page
    time.sleep(1)

    driver.execute_script("return post_form(this, 'compose', null, null, true)")



    # # Find the send button
    # send_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    # send_button.click()



def init_webdriver(login: bool, headless: bool = True):
    print("Initializing webdriver...")

    # Create the webdriver
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument('--headless')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Adding argument to disable the AutomationControlled flag
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Exclude the collection of enable-automation switches
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # Turn-off userAutomationExtension
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)

    if login:
        # Go to reddit.com
        driver.get("https://www.reddit.com/")
        time.sleep(1)

        # Delete local storage and cookies
        reddit_delete_local_storage_and_cookies(driver)

        # Login into reddit
        reddit_login(driver)

    return driver


def gpt_init_gpt():
    gptj = GPT4All("ggml-gpt4all-j-v1.3-groovy")
    return gptj


def post_resume_post(gpt, link):
    driver = init_webdriver(login=False)

    driver.get(link)
    # driver wait for 1 seconds to load the page
    time.sleep(1)

    page = driver.page_source

    soup = BeautifulSoup(page, 'html.parser')

    text_div = soup.find('div', {"data-click-id": "text"})

    # Get all the <p>
    paragraphs = text_div.find_all('p')

    text = ""

    for content in paragraphs:
        text += content.text + "\n"

    messages = [{"role": "user", "content": f"Provide a summary of the following content: {text}"}]
    gpt.chat_completion(messages)


def scrape_subreddit(subreddit, valid_posts):
    driver = init_webdriver(login=False)

    url = f"https://www.reddit.com/r/{subreddit}/new/"

    print(url)

    driver.get(url)
    # driver wait for 1 seconds to load the page
    time.sleep(1)

    page = driver.page_source
    # print(page)

    soup = BeautifulSoup(page, 'html.parser')

    # Find the posts
    posts = soup.find_all('div', {"data-testid": "post-container"})
    print(f"Found {len(posts)} posts")

    for post in posts:
        title = post.find('h3').text
        timestamp = post.find('span', {"data-testid": "post_timestamp"}).text

        __comments__ = post.find('a', {"data-click-id": "comments"}).find_all('span')
        if len(__comments__) == 0:
            comments = 0
        else:
            comments = int(post.find('a', {"data-click-id": "comments"}).find_all('span')[-1].text[0])

        if title.lower().startswith("[hiring]") or title.lower().startswith("[task]"):
            link = post.find('a', {'data-click-id': 'body'})['href']

            valid_posts.append(
                {"title": title, "link": f"https://reddit.com{link}", "timestamp": timestamp, "comments": comments})


    # Close the driver
    driver.close()


def scrape_latest_offers():

    print("Scraping latest offers...")

    subreddits = ["forhire", "freelance_forhire", "SlaveLabour_OG", "jobbit", "slavelabour", "Jobs4Bitcoins", "digitalnomad", "remotejs", "remotework"]

    valid_posts = []
    threads = [Thread(target=scrape_subreddit, args=(subreddit, valid_posts)) for subreddit in subreddits]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print(f"Found {len(valid_posts)} valid posts: {valid_posts}")
    return valid_posts


def main():
    # Open the bot
    bot = create_bot()
    # gpt = gpt_init_gpt()

    while True:
        print("Checking for new offers...")

        # Open the file
        file = open("latest_offers.txt", "r+", encoding="utf-8")
        previous_offers = file.readlines()

        print(f"Previous offers: {previous_offers}")

        latest_offers = scrape_latest_offers()

        if len(latest_offers) == 0:
            time.sleep(60)
            continue

        for offer in latest_offers:
            if f'{offer["title"]}\n' not in previous_offers:
                file.write(offer["title"] + "\n")
                file.flush()

                # post_resume_post(gpt, offer["link"])


                message = f"""
                *🔥 New offer! - {offer["title"]} 🔥*
                {offer["timestamp"]}
                
                ℹ Comments: {offer["comments"]} (Includes the sub's bot)
                {offer["link"]}
                """

                translated_message = message.translate(str.maketrans({
                    "]":  r"\]",
                    "\\": r"\\",
                    "^":  r"\^",
                    "$":  r"\$",
                    ".":  r"\.",
                    "'":  r"\'",
                    "+":  r"\+",
                    "(":  r"\(",
                    ")":  r"\)",
                    "[":  r"\[",
                    "{":  r"\{",
                    "}":  r"\}",
                    ":":  r"\:",
                    "!":  r"\!",
                    "|":  r"\|",
                    "<":  r"\<",
                    ">":  r"\>",
                    "?":  r"\?",
                    ",":  r"\,",
                    "#":  r"\#",
                    "=":  r"\=",
                    "%":  r"\%",
                    "~":  r"\~",
                    "`":  r"\`",
                    "/":  r"\/",
                    "-":  r"\-",
                    "_":  r"\_",
                    ";":  r"\;",
                }))

                # Send the announcement to the console
                print(message)

                # Send the message
                try:
                    send_bot_message(bot, translated_message)
                except Exception as e:
                    print(e)
                    traceback.print_exc()

        # Close the file
        file.close()
        print("Closing file...")
        # Sleep for 60 seconds
        time.sleep(60)

    # Stop the bot
    bot.stop_bot()


def placeholder_main():
    driver = init_webdriver(login=True, headless=False)

    # Sleep for 3 seconds
    time.sleep(3)

    # Send message to Mihai4544
    reddit_send_message_to_user(driver, "Mihai4544", "Test", "Test message")


if __name__ == "__main__":
    main()
    # placeholder_main()
