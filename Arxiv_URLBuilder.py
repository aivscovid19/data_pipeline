{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "name": "Arxiv_URLBuilder.ipynb",
      "provenance": [],
      "collapsed_sections": [],
      "authorship_tag": "ABX9TyNVXmz+wcebCsyPgfgbuxLd",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/aivscovid19/data_pipeline/blob/yeshwanth/Arxiv_URLBuilder.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "Ns1dCRVr0qzr",
        "outputId": "e8918dcc-9a27-47be-bee3-347c6852a80d",
        "colab": {
          "base_uri": "https://localhost:8080/",
          "height": 1000
        }
      },
      "source": [
        "# Installing Centaurminer chrome driver\n",
        "!pip install centaurMiner==0.0.8\n",
        "# Colab only: This is normally done automatically\n",
        "!apt-get update # update ubuntu to correctly run apt-install\n",
        "!apt install chromium-chromedriver # Installs to '/usr/lib/chromium-browser/chromedriver'\n",
        "import time\n",
        "import pandas_gbq\n",
        "import pandas as pd\n",
        "from datetime import datetime"
      ],
      "execution_count": null,
      "outputs": [
        {
          "output_type": "stream",
          "text": [
            "Collecting centaurMiner==0.0.8\n",
            "  Downloading https://files.pythonhosted.org/packages/54/5c/bfaf41514e9439d61d5f31ae4ab685cf8ab178a57e4d7dbc310125d669ee/centaurminer-0.0.8-py3-none-any.whl\n",
            "Collecting selenium\n",
            "\u001b[?25l  Downloading https://files.pythonhosted.org/packages/80/d6/4294f0b4bce4de0abf13e17190289f9d0613b0a44e5dd6a7f5ca98459853/selenium-3.141.0-py2.py3-none-any.whl (904kB)\n",
            "\u001b[K     |████████████████████████████████| 911kB 10.0MB/s \n",
            "\u001b[?25hCollecting webdriver-manager\n",
            "  Downloading https://files.pythonhosted.org/packages/2a/88/bc1f85fd733cf6bcae3c6e5c86ea124e91c49eb694d47dfef7f37f4394eb/webdriver_manager-3.2.2-py2.py3-none-any.whl\n",
            "Requirement already satisfied: urllib3 in /usr/local/lib/python3.6/dist-packages (from selenium->centaurMiner==0.0.8) (1.24.3)\n",
            "Collecting crayons\n",
            "  Downloading https://files.pythonhosted.org/packages/5b/0d/e3fad4ca1de8e70e06444e7d777a5984261e1db98758b5be3e8296c03fe9/crayons-0.4.0-py2.py3-none-any.whl\n",
            "Collecting configparser\n",
            "  Downloading https://files.pythonhosted.org/packages/4b/6b/01baa293090240cf0562cc5eccb69c6f5006282127f2b846fad011305c79/configparser-5.0.0-py3-none-any.whl\n",
            "Requirement already satisfied: requests in /usr/local/lib/python3.6/dist-packages (from webdriver-manager->centaurMiner==0.0.8) (2.23.0)\n",
            "Collecting colorama\n",
            "  Downloading https://files.pythonhosted.org/packages/c9/dc/45cdef1b4d119eb96316b3117e6d5708a08029992b2fee2c143c7a0a5cc5/colorama-0.4.3-py2.py3-none-any.whl\n",
            "Requirement already satisfied: chardet<4,>=3.0.2 in /usr/local/lib/python3.6/dist-packages (from requests->webdriver-manager->centaurMiner==0.0.8) (3.0.4)\n",
            "Requirement already satisfied: idna<3,>=2.5 in /usr/local/lib/python3.6/dist-packages (from requests->webdriver-manager->centaurMiner==0.0.8) (2.10)\n",
            "Requirement already satisfied: certifi>=2017.4.17 in /usr/local/lib/python3.6/dist-packages (from requests->webdriver-manager->centaurMiner==0.0.8) (2020.6.20)\n",
            "Installing collected packages: selenium, colorama, crayons, configparser, webdriver-manager, centaurMiner\n",
            "Successfully installed centaurMiner-0.0.8 colorama-0.4.3 configparser-5.0.0 crayons-0.4.0 selenium-3.141.0 webdriver-manager-3.2.2\n",
            "Hit:1 http://archive.ubuntu.com/ubuntu bionic InRelease\n",
            "Get:2 http://security.ubuntu.com/ubuntu bionic-security InRelease [88.7 kB]\n",
            "Get:3 http://archive.ubuntu.com/ubuntu bionic-updates InRelease [88.7 kB]\n",
            "Get:4 http://ppa.launchpad.net/c2d4u.team/c2d4u4.0+/ubuntu bionic InRelease [15.9 kB]\n",
            "Hit:5 http://ppa.launchpad.net/graphics-drivers/ppa/ubuntu bionic InRelease\n",
            "Get:6 https://cloud.r-project.org/bin/linux/ubuntu bionic-cran40/ InRelease [3,626 B]\n",
            "Get:7 http://archive.ubuntu.com/ubuntu bionic-backports InRelease [74.6 kB]\n",
            "Ign:8 https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64  InRelease\n",
            "Ign:9 https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64  InRelease\n",
            "Get:10 https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64  Release [697 B]\n",
            "Hit:11 https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64  Release\n",
            "Get:12 https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64  Release.gpg [836 B]\n",
            "Get:13 http://security.ubuntu.com/ubuntu bionic-security/multiverse amd64 Packages [14.6 kB]\n",
            "Get:14 http://security.ubuntu.com/ubuntu bionic-security/restricted amd64 Packages [193 kB]\n",
            "Get:15 http://security.ubuntu.com/ubuntu bionic-security/main amd64 Packages [1,693 kB]\n",
            "Get:16 http://security.ubuntu.com/ubuntu bionic-security/universe amd64 Packages [1,332 kB]\n",
            "Get:17 http://archive.ubuntu.com/ubuntu bionic-updates/universe amd64 Packages [2,095 kB]\n",
            "Get:18 http://archive.ubuntu.com/ubuntu bionic-updates/restricted amd64 Packages [220 kB]\n",
            "Get:19 http://archive.ubuntu.com/ubuntu bionic-updates/multiverse amd64 Packages [44.6 kB]\n",
            "Get:20 http://archive.ubuntu.com/ubuntu bionic-updates/main amd64 Packages [2,110 kB]\n",
            "Get:21 http://ppa.launchpad.net/c2d4u.team/c2d4u4.0+/ubuntu bionic/main Sources [1,673 kB]\n",
            "Get:22 http://ppa.launchpad.net/c2d4u.team/c2d4u4.0+/ubuntu bionic/main amd64 Packages [856 kB]\n",
            "Get:23 https://cloud.r-project.org/bin/linux/ubuntu bionic-cran40/ Packages [36.0 kB]\n",
            "Get:24 http://archive.ubuntu.com/ubuntu bionic-backports/main amd64 Packages [11.3 kB]\n",
            "Get:25 http://archive.ubuntu.com/ubuntu bionic-backports/universe amd64 Packages [11.4 kB]\n",
            "Ign:27 https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64  Packages\n",
            "Get:27 https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64  Packages [306 kB]\n",
            "Fetched 10.9 MB in 3s (4,332 kB/s)\n",
            "Reading package lists... Done\n",
            "Reading package lists... Done\n",
            "Building dependency tree       \n",
            "Reading state information... Done\n",
            "The following additional packages will be installed:\n",
            "  chromium-browser chromium-browser-l10n chromium-codecs-ffmpeg-extra\n",
            "Suggested packages:\n",
            "  webaccounts-chromium-extension unity-chromium-extension adobe-flashplugin\n",
            "The following NEW packages will be installed:\n",
            "  chromium-browser chromium-browser-l10n chromium-chromedriver\n",
            "  chromium-codecs-ffmpeg-extra\n",
            "0 upgraded, 4 newly installed, 0 to remove and 23 not upgraded.\n",
            "Need to get 79.2 MB of archives.\n",
            "After this operation, 268 MB of additional disk space will be used.\n",
            "Get:1 http://archive.ubuntu.com/ubuntu bionic-updates/universe amd64 chromium-codecs-ffmpeg-extra amd64 85.0.4183.121-0ubuntu0.18.04.1 [1,117 kB]\n",
            "Get:2 http://archive.ubuntu.com/ubuntu bionic-updates/universe amd64 chromium-browser amd64 85.0.4183.121-0ubuntu0.18.04.1 [70.3 MB]\n",
            "Get:3 http://archive.ubuntu.com/ubuntu bionic-updates/universe amd64 chromium-browser-l10n all 85.0.4183.121-0ubuntu0.18.04.1 [3,432 kB]\n",
            "Get:4 http://archive.ubuntu.com/ubuntu bionic-updates/universe amd64 chromium-chromedriver amd64 85.0.4183.121-0ubuntu0.18.04.1 [4,415 kB]\n",
            "Fetched 79.2 MB in 1s (55.4 MB/s)\n",
            "Selecting previously unselected package chromium-codecs-ffmpeg-extra.\n",
            "(Reading database ... 144619 files and directories currently installed.)\n",
            "Preparing to unpack .../chromium-codecs-ffmpeg-extra_85.0.4183.121-0ubuntu0.18.04.1_amd64.deb ...\n",
            "Unpacking chromium-codecs-ffmpeg-extra (85.0.4183.121-0ubuntu0.18.04.1) ...\n",
            "Selecting previously unselected package chromium-browser.\n",
            "Preparing to unpack .../chromium-browser_85.0.4183.121-0ubuntu0.18.04.1_amd64.deb ...\n",
            "Unpacking chromium-browser (85.0.4183.121-0ubuntu0.18.04.1) ...\n",
            "Selecting previously unselected package chromium-browser-l10n.\n",
            "Preparing to unpack .../chromium-browser-l10n_85.0.4183.121-0ubuntu0.18.04.1_all.deb ...\n",
            "Unpacking chromium-browser-l10n (85.0.4183.121-0ubuntu0.18.04.1) ...\n",
            "Selecting previously unselected package chromium-chromedriver.\n",
            "Preparing to unpack .../chromium-chromedriver_85.0.4183.121-0ubuntu0.18.04.1_amd64.deb ...\n",
            "Unpacking chromium-chromedriver (85.0.4183.121-0ubuntu0.18.04.1) ...\n",
            "Setting up chromium-codecs-ffmpeg-extra (85.0.4183.121-0ubuntu0.18.04.1) ...\n",
            "Setting up chromium-browser (85.0.4183.121-0ubuntu0.18.04.1) ...\n",
            "update-alternatives: using /usr/bin/chromium-browser to provide /usr/bin/x-www-browser (x-www-browser) in auto mode\n",
            "update-alternatives: using /usr/bin/chromium-browser to provide /usr/bin/gnome-www-browser (gnome-www-browser) in auto mode\n",
            "Setting up chromium-chromedriver (85.0.4183.121-0ubuntu0.18.04.1) ...\n",
            "Setting up chromium-browser-l10n (85.0.4183.121-0ubuntu0.18.04.1) ...\n",
            "Processing triggers for hicolor-icon-theme (0.17-2) ...\n",
            "Processing triggers for mime-support (3.60ubuntu1) ...\n",
            "Processing triggers for man-db (2.8.3-2ubuntu0.1) ...\n"
          ],
          "name": "stdout"
        }
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "4zo_tnYM4rDg"
      },
      "source": [
        "import centaurminer as mining"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "S-gdqtF41_PD",
        "outputId": "1973518d-3e3b-42fe-c3f8-acf16fdcbb2a",
        "colab": {
          "base_uri": "https://localhost:8080/",
          "height": 33
        }
      },
      "source": [
        "from google.colab import auth      # Google Authentication\n",
        "auth.authenticate_user()\n",
        "print('Authenticated')"
      ],
      "execution_count": null,
      "outputs": [
        {
          "output_type": "stream",
          "text": [
            "Authenticated\n"
          ],
          "name": "stdout"
        }
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "AVbcLoZy4RLU"
      },
      "source": [
        "project_id='for-yr'\n",
        "table_id=f'Medical_Dataset.arxiv'\n",
        "schema = [\n",
        "    {'name': 'article_url', 'type': 'STRING',   'mode': 'REQUIRED'},\n",
        "    {'name': 'catalog_url', 'type': 'STRING',   'mode': 'REQUIRED'},\n",
        "    {'name': 'is_pdf',      'type': 'INT64',    'mode': 'REQUIRED'},\n",
        "    {'name': 'language',    'type': 'STRING'                      },\n",
        "    {'name': 'status',      'type': 'STRING',   'mode': 'REQUIRED'},\n",
        "    {'name': 'timestamp',   'type': 'DATETIME', 'mode': 'REQUIRED'},\n",
        "    {'name': 'worker_id',   'type': 'STRING'                      },\n",
        "    {'name': 'meta_info',   'type': 'STRING'                      }\n",
        "]"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "rqcPY0fW2SA8"
      },
      "source": [
        "class URL_builder():\n",
        "  \"\"\" \n",
        "        Class to get the urls from the site with a search_word. \n",
        "  \n",
        "        Parameters:\n",
        "          search_word: word to be searched for urls. \n",
        "          * If the search_word consists of two words like social distancing,\n",
        "            use +AND+Social+distancing\n",
        "            Sample link would look this:\n",
        "                      http://export.arxiv.org/find/all/1/all:+AND+Social+distancing/0/1/0/all/0/1?skip=0&query_id=c292936257c7949e\n",
        "\n",
        "          \n",
        "          pages: Number of pages from which the urls need to extracted.\n",
        "          * Each page consists of only 25 articles.\n",
        "  \"\"\"\n",
        "  def __init__(self,search_word,pages):\n",
        "    \"\"\" \n",
        "        Class to get the urls from the site with a search_word. \n",
        "  \n",
        "        Parameters:\n",
        "          search_word: word to be searched for urls. \n",
        "          * If the search_word consists of two words like social distancing,\n",
        "            use +AND+Social+distancing\n",
        "            Sample link would look this:\n",
        "                      http://export.arxiv.org/find/all/1/all:+AND+Social+distancing/0/1/0/all/0/1?skip=0&query_id=c292936257c7949e\n",
        "\n",
        "          \n",
        "          pages: Number of pages from which the urls need to extracted.\n",
        "          * Each page consists of only 25 articles.\n",
        "    \"\"\"\n",
        "    driver_path = '/usr/lib/chromium-browser/chromedriver'\n",
        "    url_search=f\"http://export.arxiv.org/find/all/1/all:+{search_word}/0/1/0/all/0/1?skip=\".format(search_word)\n",
        "    article_set = set()\n",
        "    self.url1=[]\n",
        "    self.url_schema=pd.DataFrame()\n",
        "    for page_num in range(0,25*(pages),25):\n",
        "      print(f\"Getting URLs from {page_num + 1}...\", flush=True)\n",
        "      url=url_search+str(page_num)#+f\"&query_id={query_id}\".format(query_id)\n",
        "      articles = mining.Element(\"css_selector\",\"span.list-identifier > a\").get_attribute('href')\n",
        "      urls = mining.CollectURLs(url, articles,maxElems=20, driver_path=driver_path)\n",
        "      [self.url1.append(i) for i in urls if 'abs' in i]\n",
        "      self.url_schema['article_url']= self.url1\n",
        "      self.url_schema['catalog_url']=url\n",
        "      [article_set.add(i) for i in urls if 'abs' in i]\n",
        "    self.url_schema['is_pdf']=0\n",
        "    self.url_schema['language']='en'\n",
        "    self.url_schema['status']='not mined'\n",
        "    self.url_schema['timestamp']= datetime.utcnow()\n",
        "    self.url_schema['worker_id']=None\n",
        "    self.url_schema['meta_info']=None\n",
        "    print(\"Total of \" + str(len(article_set)) + \" articles\")\n",
        "  \n",
        "\n",
        "  def bigquery(self,project_id,table_id,schema):\n",
        "\n",
        "    \"\"\" \n",
        "        Function to push the urls to the bigquery. \n",
        "  \n",
        "        Parameters:\n",
        "          project_id: project_id in bigquery. \n",
        "          table_id: table name.\n",
        "          schema: schema to be followed.\n",
        "    \"\"\" \n",
        "    # Append the new urls to the existing table\n",
        "    pandas_gbq.to_gbq(self.new_urls, table_id, project_id=project_id, if_exists='append', table_schema=schema)\n",
        "    return self.url_schema"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "qka4A8vQ4VjQ",
        "outputId": "7ccf898a-b920-468c-cf44-549271a671ef",
        "colab": {
          "base_uri": "https://localhost:8080/",
          "height": 831
        }
      },
      "source": [
        "urls=URL_builder('coronavirus',1)\n",
        "urls.bigquery(project_id,table_id,schema)"
      ],
      "execution_count": null,
      "outputs": [
        {
          "output_type": "stream",
          "text": [
            "Getting URLs from 1...\n",
            "Headless: True\n",
            "driver path: /usr/lib/chromium-browser/chromedriver\n",
            "Total of 25 articles\n"
          ],
          "name": "stdout"
        },
        {
          "output_type": "execute_result",
          "data": {
            "text/html": [
              "<div>\n",
              "<style scoped>\n",
              "    .dataframe tbody tr th:only-of-type {\n",
              "        vertical-align: middle;\n",
              "    }\n",
              "\n",
              "    .dataframe tbody tr th {\n",
              "        vertical-align: top;\n",
              "    }\n",
              "\n",
              "    .dataframe thead th {\n",
              "        text-align: right;\n",
              "    }\n",
              "</style>\n",
              "<table border=\"1\" class=\"dataframe\">\n",
              "  <thead>\n",
              "    <tr style=\"text-align: right;\">\n",
              "      <th></th>\n",
              "      <th>article_url</th>\n",
              "      <th>catalog_url</th>\n",
              "      <th>is_pdf</th>\n",
              "      <th>language</th>\n",
              "      <th>status</th>\n",
              "      <th>timestamp</th>\n",
              "      <th>worker_id</th>\n",
              "      <th>meta_info</th>\n",
              "    </tr>\n",
              "  </thead>\n",
              "  <tbody>\n",
              "    <tr>\n",
              "      <th>0</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.13577</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>1</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.12923</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>2</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.12817</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>3</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.12698</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>4</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.12500</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>5</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.12176</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>6</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.12076</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>7</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.11714</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>8</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.11288</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>9</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.11008</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>10</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.10931</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>11</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.10648</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>12</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.10474</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>13</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.10141</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>14</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.09926</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>15</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.09911</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>16</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.09076</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>17</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.09074</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>18</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.08862</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>19</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.08831</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>20</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.08573</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>21</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.08369</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>22</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.07652</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>23</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.07627</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "    <tr>\n",
              "      <th>24</th>\n",
              "      <td>http://export.arxiv.org/abs/2009.07403</td>\n",
              "      <td>http://export.arxiv.org/find/all/1/all:+corona...</td>\n",
              "      <td>0</td>\n",
              "      <td>en</td>\n",
              "      <td>not mined</td>\n",
              "      <td>2020-09-30 14:39:45.597776</td>\n",
              "      <td>None</td>\n",
              "      <td>None</td>\n",
              "    </tr>\n",
              "  </tbody>\n",
              "</table>\n",
              "</div>"
            ],
            "text/plain": [
              "                               article_url  ... meta_info\n",
              "0   http://export.arxiv.org/abs/2009.13577  ...      None\n",
              "1   http://export.arxiv.org/abs/2009.12923  ...      None\n",
              "2   http://export.arxiv.org/abs/2009.12817  ...      None\n",
              "3   http://export.arxiv.org/abs/2009.12698  ...      None\n",
              "4   http://export.arxiv.org/abs/2009.12500  ...      None\n",
              "5   http://export.arxiv.org/abs/2009.12176  ...      None\n",
              "6   http://export.arxiv.org/abs/2009.12076  ...      None\n",
              "7   http://export.arxiv.org/abs/2009.11714  ...      None\n",
              "8   http://export.arxiv.org/abs/2009.11288  ...      None\n",
              "9   http://export.arxiv.org/abs/2009.11008  ...      None\n",
              "10  http://export.arxiv.org/abs/2009.10931  ...      None\n",
              "11  http://export.arxiv.org/abs/2009.10648  ...      None\n",
              "12  http://export.arxiv.org/abs/2009.10474  ...      None\n",
              "13  http://export.arxiv.org/abs/2009.10141  ...      None\n",
              "14  http://export.arxiv.org/abs/2009.09926  ...      None\n",
              "15  http://export.arxiv.org/abs/2009.09911  ...      None\n",
              "16  http://export.arxiv.org/abs/2009.09076  ...      None\n",
              "17  http://export.arxiv.org/abs/2009.09074  ...      None\n",
              "18  http://export.arxiv.org/abs/2009.08862  ...      None\n",
              "19  http://export.arxiv.org/abs/2009.08831  ...      None\n",
              "20  http://export.arxiv.org/abs/2009.08573  ...      None\n",
              "21  http://export.arxiv.org/abs/2009.08369  ...      None\n",
              "22  http://export.arxiv.org/abs/2009.07652  ...      None\n",
              "23  http://export.arxiv.org/abs/2009.07627  ...      None\n",
              "24  http://export.arxiv.org/abs/2009.07403  ...      None\n",
              "\n",
              "[25 rows x 8 columns]"
            ]
          },
          "metadata": {
            "tags": []
          },
          "execution_count": 14
        }
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "N_7cWIQfzdpD"
      },
      "source": [
        ""
      ],
      "execution_count": null,
      "outputs": []
    }
  ]
}