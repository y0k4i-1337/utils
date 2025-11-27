#!/usr/bin/env python3
import argparse
import xml.etree.ElementTree as ET
import base64
import json
import sys
import re
import binascii

def extract_json_from_http_response(http_response):
    pattern = re.compile(r'^\s*[{\[]', re.MULTILINE)
    match = pattern.search(http_response)
    if match:
        json_content = http_response[match.start():]
        return json_content
    return None

def decode_and_convert_to_json(base64_encoded_response, verbose=False):
    try:
        decoded_bytes = base64.b64decode(base64_encoded_response)
        decoded_string = decoded_bytes.decode('utf-8')
        if verbose:
            print(f"Decoded response: {decoded_string[:100]}...", file=sys.stderr)
        json_content = extract_json_from_http_response(decoded_string)
        if verbose:
            print(f"Extracted JSON content: {json_content[:100]}..." if json_content else "No JSON content found.", file=sys.stderr)
        if json_content:
            return json.loads(json_content)
        else:
            return None
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"Error decoding or parsing response: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Extract JSON content from base64-encoded responses in an XML file.")
    parser.add_argument("input_file", help="Input XML file containing base64-encoded responses")
    parser.add_argument("--output_file", help="Output JSON file (default: print to stdout)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    try:
        tree = ET.parse(args.input_file)
        root = tree.getroot()

        responses = []
        all_responses = root.findall('.//response')
        if args.verbose:
            print(f"Found {len(all_responses)} response elements in the XML.", file=sys.stderr)
        for response_elem in all_responses:
            base64_encoded = response_elem.text
            if not base64_encoded:
                if args.verbose:
                    print("Empty response element found, skipping.", file=sys.stderr)
                continue
            if args.verbose:
                print(f"Processing response: {base64_encoded[:30]}...", file=sys.stderr)
            response_json = decode_and_convert_to_json(base64_encoded, verbose=args.verbose)
            if response_json:
                # if list, add each item separately
                if isinstance(response_json, list):
                    for item in response_json:
                        responses.append(item)
                else:
                    responses.append(response_json)

        if args.output_file:
            with open(args.output_file, 'w') as output_file:
                json.dump(responses, output_file, indent=2)
        else:
            print(json.dumps(responses, indent=2))

    except (FileNotFoundError, ET.ParseError) as e:
        print(f"Error reading or parsing input XML: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
