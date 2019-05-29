#!/bin/python3

import requests
from bs4 import BeautifulSoup
import snip
import loom
import os
# import re
# from pprint import pprint


urlbase = "https://godotengine.org"


def getSoup(url, base=""):
    with snip.timer():
        req = requests.get(base + url)
        soup = BeautifulSoup(req.text, features="html.parser")
        print("Got '{}' in".format(url), end=" ")
    return soup


def processSoupItem(item_soup, assetlib):
    try:
        name = item_soup.find("h4").find("a").text
        # print(name)
        gver = item_soup.find("span", class_="label-danger")
        info = item_soup.find("span", class_="label-info")
        item = {
            "name": name,
            "version": item_soup.find("small").text,
            "author": item_soup.find("a", title=True).text,
            "url": item_soup.find("h4").find("a").get("href"),
            "category": item_soup.find("span", class_="label-primary").text,
            "gver": gver.text if gver else None,
            "info": info.text if info else None,
            "date": item_soup.findAll("span", class_="nowrap")[-1].text

        }

        item_soup_2 = getSoup(item["url"], urlbase)
        item["download"] = item_soup_2.find("a", class_="btn btn-primary").get("href")

        assetlib.append(item)
    except AttributeError:
        print("Error with item")
        print(item_soup)


def getAssetLib():

    assetlib = []

    pagei = 0
    urlfmtstr = "/asset-library/asset?max_results=200&page={pagei}&sort=cost"

    with loom.Spool(8, "URLs") as downloadurlspool:

        while True:
            print("Getting page", pagei)
            soup = getSoup(urlfmtstr.format(pagei=pagei), urlbase)

            items = soup.findAll("div", class_="asset-item")
            if not items:
                break
            for item_soup in items:
                downloadurlspool.enqueue(processSoupItem, (item_soup, assetlib,))
            pagei += 1
            # break

    return assetlib


def saveFileAs(url, parentDir):
    filename = snip.easySlug(os.path.split(url)[1])
    localpath = os.path.join(parentDir, filename)
    if not os.path.exists(localpath):
        os.makedirs(parentDir, exist_ok=True)
        print(url, "->", localpath)
        request = requests.get(url)
        with open(localpath, 'wb') as fd:
            for chunk in request.iter_content(chunk_size=128):
                fd.write(chunk)


def downloadAsset(item):
    name = " - ".join([snip.easySlug(item[f]) for f in ["author", "name", "version"]])
    localdir = os.path.join("assetstore", item["category"], name)
    saveFileAs(item["download"], localdir)


if __name__ == "__main__":

    print("Getting asset library")
    assetlib = getAssetLib()

    with loom.Spool(8, "Download") as spool:
        for item in assetlib:
            spool.enqueue(downloadAsset, (item,))
