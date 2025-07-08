from flask import jsonify

def error_response(message, code=400):
    return jsonify({"error": message}), code