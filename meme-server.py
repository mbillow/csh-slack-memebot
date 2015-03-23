from flask import Flask, request, jsonify
from urllib import unquote
import ConfigParser
import logging
import argparse

config = ConfigParser.ConfigParser()
logging.basicConfig(filename='server.log', level=logging.DEBUG)


def read_config():
    config.read('bot_config.cfg')
    global token_key, meme_list, channel_list
    token_key = config.get("API_KEYS", "BOT_KEY")
    meme_list = config.options("MEME_LIST")
    channel_list = {}
    for channel in config.options("CHANNELS"):
        channel_list[channel] = config.getboolean("CHANNELS", channel)


def create_dict(data):
    request_dict = {}
    item_list = data.split("&")
    for item in item_list:
        split_item = item.split("=")
        request_dict[split_item[0]] = unquote(split_item[1]).replace("+", " ")
    return request_dict


def list_memes(list_format="string"):
    read_config()
    string_list = "Currently available memes:\n"
    if list_format == "string":
        for meme in meme_list:
            string_list += meme + "\n"
        return string_list
    elif list_format == "list":
        return meme_list


def verify_command(key):
    read_config()
    if key == token_key:
        return True
    else:
        return False


def add_meme(command):
    meme_params = unquote(command).split("#")
    if not meme_params[1] in list_memes("list"):
        config_file = open("bot_config.cfg", "a")
        config_file.write(meme_params[1] + "=" + (meme_params[2]).strip()[1:-1] + "\n")
        config_file.close()
        read_config()
        return "Meme added to bot!"
    elif meme_params[1] in list_memes("list"):
        return "Meme already exists!"


app = Flask(__name__)

@app.route("/slack", methods=["POST"])
def incoming_request():
    if request.method == "POST":
        inc_req = request.get_data()
        request_data = create_dict(inc_req)
        read_config()
        info = lambda action: logging.info("User: {} -- {}".format(request_data["user_name"], action)
        
        if verify_command(request_data["token"]):
            requested = (request_data["text"].split(":")[1].strip())
            if requested == "list":
                meme_json = jsonify({'text': list_memes()})
                info("Request: List")
            elif requested.startswith("add"):
                meme_json = jsonify({'text': add_meme(request_data["text"])})
                info("Added Meme")
            elif requested in meme_list and channel_list[request_data["channel_name"]]:
                meme_json = jsonify({'text': config.get("MEME_LIST", requested)})
                info("Send Meme: {}".format(requested))
            elif not channel_list[request_data["channel_name"]]:
                meme_json = jsonify({'text': "Memes have been disabled in this channel."})
            else:
                meme_json = jsonify({'text': "No meme found, feel free to add it though!"})
                logging.warning("User: {} -- Meme: {} not found", request_data["user_name"], requested)
            print meme_json
            return meme_json



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test",
                        help="Runs the server in test mode and updates the"
                             " testUsers database.",
                        action="store_true")

    args = parser.parse_args()

    app.run(host='0.0.0.0', port=42011, debug=args.test)
