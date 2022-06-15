from typing import Container
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import time
import uuid


class LastManStandsScraper:
    def __init__(self):
        self.URL = (
            "https://www.lastmanstands.com/team-profile/t20/?teamid=20327")
        self.master_list = []

    def _load_and_accept_cookies(self) -> webdriver.Chrome:
        '''
        Open Last Man Stands Site and accept cookies

        Returns
        -------
        self.driver: webdriver.Chrome

        '''
        self.driver = webdriver.Chrome()

        (self.driver).get(self.URL)
        delay = 10
        try:
            WebDriverWait(self.driver, delay).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="gdpr-popup-container"]')))
            print("Frame Ready!")
            accept_cookies_button = WebDriverWait(self.driver, delay).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="gdpr-accept-btn"]')))
            print("Accept Cookies Button Ready!")
            accept_cookies_button.click()
            time.sleep(1)
        except TimeoutException:
            print("Loading took too much time!")

    def _get_player_list_container(self) -> Container:
        '''
        Returns a container containing all player information
        Parameters
        ----------
        driver: webdriver.Chrome
            The driver that contains information about the current page

        Returns
        -------
        player_list_container: a container within which all player information is contained
        '''

        # finds the container within which the full list of player links are contained
        batting_button = (self.driver).find_element(
            By.XPATH, '//*[@id="tp-sm-batting"]')
        batting_button.click()

        delay = 10
        try:
            WebDriverWait(self.driver, delay).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="team-profile-2021-batting-stats"]')))
            player_link_container = self.driver.find_element(
                By.XPATH, '//*[@id="team-profile-2021-batting-stats"]')
            time.sleep(1)
        except TimeoutException:
            print("Loading took too much time!")
        player_link_body = player_link_container.find_element(
            By.XPATH, './tbody')
        self.player_list_container = player_link_body.find_elements(By.XPATH,
                                                                    './/tr')

    def _create_master_list(self) -> list:
        '''_create_master_list creates template for the list where collceted data will be stored
        Adds Player Name and Player Link to each unique entry.

        Returns:
            master_list: list with template for data storage
        '''

        for row in self.player_list_container:
            name = row.find_element(By.TAG_NAME, 'a').text
            a_tag = row.find_element(By.TAG_NAME, 'a')
            link = a_tag.get_attribute('href')
            player_dictionary = {"PlayerName": name, "UUID": str(
                uuid.uuid4()), "PlayerLink": link, "ScorecardIds": [], "ScorecardBattingData": [], "ScorecardBowlingData": [], "Awards": {"MostValuablePlayer": 0, "MostValuableBatter": 0, "MostValuableBowler": 0}}
            self.master_list.append(player_dictionary)

        print(self.master_list)

    def _collect_scoreboard_ids(self):
        '''_collect_scoreboard_ids 
        1. Load each Player Link
        2. Navigate to Scorecard Link
        3. Collect list of scorecard links and add to player dictionary

        '''

        for player_dictionary in self.master_list:
            (self.driver).get(player_dictionary['PlayerLink'])
            ((self.driver).find_element(By.XPATH,
             '//*[@id="pp-sm-batting"]')).click()
            ((self.driver).find_element(By.XPATH,
             '//*[@id="batting-history-link-current"]')).click()
            self._get_scoreboard_ids()
            player_dictionary['ScorecardIds'].append(
                self.scorecard_id_list)

    def _get_scoreboard_ids(self) -> list:
        '''_get_scoreboard_ids 
        1. Wait for the player game table to load.
        2. Once loaded locate and create a list of scoreboard links on that page.

        Returns:
            a list of scoreboard links
        '''

        delay = 10
        try:
            WebDriverWait(self.driver, delay).until(EC.presence_of_element_located(
                (By.XPATH, '//table[@class="rank-table"]')))
            scorecard_container = (self.driver).find_element(
                By.XPATH, '//table[@class="rank-table"]')
            time.sleep(1)
        except TimeoutException:
            print("Loading took too much time!")

        scorecard_container_body = scorecard_container.find_element(
            By.XPATH, './tbody')
        scorecard_container_list = scorecard_container_body.find_elements(
            By.XPATH, './tr')
        self.scorecard_id_list = []

        for row in scorecard_container_list:
            a_tag = row.find_element(By.TAG_NAME, 'a')
            link = a_tag.get_attribute('href')
            fixture_id = (link.split("="))[1]
            self.scorecard_id_list.append(fixture_id)

    def _retrieve_all_player_data(self):

        self.test_list = [{'PlayerName': 'Freddie Simon', 'UUID': '62dafa1f-3fc9-428f-bce1-afba3c579853', 'PlayerLink': 'https://www.lastmanstands.com/cricket-player/t20?playerid=291389',
                           'ScorecardIds': [['345123', '345121']], 'ScorecardBattingData': [], 'ScorecardBowlingData': [], "Awards": {"MostValuablePlayer": 0, "MostValuableBatter": 0, "MostValuableBowler": 0}}]

        for player_dictionary in self.master_list:
            for id_list in player_dictionary['ScorecardIds']:
                for id in id_list:
                    ((self.driver)).get(
                        f"https://www.lastmanstands.com/leagues/scorecard/1st-innings?fixtureid={id}")
                    self._get_scorecard_player_data(player_dictionary)
                    ((self.driver)).get(
                        f"https://www.lastmanstands.com/leagues/scorecard/2nd-innings?fixtureid={id}")
                    self._get_scorecard_player_data(player_dictionary)
                    ((self.driver)).get(
                        f"https://www.lastmanstands.com/leagues/scorecard/stats?fixtureid={id}")
                    self._get_player_awards(player_dictionary)

    def _get_scorecard_player_data(self, player_dictionary):

        # Create tables for battings data and bowling data
        scorecard_data_table_list = (self.driver).find_elements(
            By.XPATH, './/table')

        batting_data_body = scorecard_data_table_list[0].find_element(
            By.XPATH, './tbody')
        batting_data_list = batting_data_body.find_elements(
            By.XPATH, './tr')

        bowling_data_body = scorecard_data_table_list[1].find_element(
            By.XPATH, './tbody')
        bowling_data_list = bowling_data_body.find_elements(
            By.XPATH, './tr')

        # If name exists in batting data - find data

        for row in batting_data_list:
            try:
                player_name = row.find_element(By.TAG_NAME, 'a').text
                if player_name == player_dictionary["PlayerName"]:
                    print("Name found")
                    data_list = row.find_elements(By.XPATH, './td')
                    batting_dictionary = {"How Out": (data_list[0].text).split("\n")[1], "Runs": data_list[1].text, "Balls": data_list[2].text,
                                          "Fours": data_list[3].text, "Sixs": data_list[4].text, "SR": data_list[5].text}
                    player_dictionary["ScorecardBattingData"].append(
                        batting_dictionary)
            except NoSuchElementException:
                continue

        # If name exists in bowling data - find data

        for row in bowling_data_list:
            try:
                player_name = row.find_element(By.TAG_NAME, 'a').text
                if player_name == player_dictionary["PlayerName"]:
                    print("Name found")
                    data_list = row.find_elements(By.XPATH, './td')
                    bowling_dictionary = {"Overs": data_list[1].text, "Runs": data_list[2].text,
                                          "Wickets": data_list[3].text, "Maidens": data_list[4].text, "Economy": data_list[5].text}
                    player_dictionary["ScorecardBowlingData"].append(
                        bowling_dictionary)
            except NoSuchElementException:
                continue

    def _get_player_awards(self, player_dictionary):

        self._get_most_valuable_player_award(player_dictionary)
        self._get_most_valuable_batter_award(player_dictionary)
        self._get_most_valuable_bowler_award(player_dictionary)

    def _get_most_valuable_player_award(self, player_dictionary):
        mvp_container = (self.driver).find_element(
            By.XPATH, '//div[@id="scorecard-2020-stats-block-mvp"]')
        mvp_list = mvp_container.find_elements(By.XPATH, './div')
        for item in mvp_list:
            try:
                player_name = item.text
                if player_name == player_dictionary["PlayerName"]:
                    (player_dictionary["Awards"])["MostValuablePlayer"] += 1
                    break
                else:
                    continue

            except NoSuchElementException:
                continue

    def _get_most_valuable_batter_award(self, player_dictionary):
        mvb_container = (self.driver).find_element(
            By.XPATH, '//div[@id="scorecard-2020-stats-block-mvbat"]')
        mvb_list = mvb_container.find_elements(By.XPATH, './div')
        for item in mvb_list:
            try:
                player_name = item.text
                if player_name == player_dictionary["PlayerName"]:
                    (player_dictionary["Awards"])["MostValuableBatter"] += 1
                    break
                else:
                    continue

            except NoSuchElementException:
                continue

    def _get_most_valuable_bowler_award(self, player_dictionary):
        mvb_container = (self.driver).find_element(
            By.XPATH, '//div[@id="scorecard-2020-stats-block-mvbowl"]')
        mvb_list = mvb_container.find_elements(By.XPATH, './div')
        for item in mvb_list:
            try:
                player_name = item.text
                if player_name == player_dictionary["PlayerName"]:
                    (player_dictionary["Awards"])["MostValuableBowler"] += 1
                    break
                else:
                    continue

            except NoSuchElementException:
                continue

    def run_crawler(self):
        self._load_and_accept_cookies()
        self._get_player_list_container()
        self._create_master_list()
        self._collect_scoreboard_ids()
        self._retrieve_all_player_data()
        print(self.master_list)


def run():
    crawler = LastManStandsScraper()
    crawler.run_crawler()


if __name__ == "__main__":

    run()
