#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
app = Flask(__name__)


@app.route("/")
def main():
    return render_template('index.html')

@app.route("/audio/<path:filename>")
def audio(filename):
    return send_from_directory("audio", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, extra_files="./images")
