import argparse
import datetime
import json
import sys
from file2txt.openai_processor import OpenAIMDCleaner
from file2txt.parsers.core import BaseParser
from file2txt import convert_file

import logging
from os.path import isdir
import os.path
from pathlib import Path
import dotenv

# logging.basicConfig(level=logging.DEBUG)

def str_to_bool(value: str) -> bool:
    match value.lower():
        case 'yes' | 'true' | 't' | 'y' | '1':
            return True
        case 'no' | 'false' | 'f' | 'n' | '0':
            return False
        case _:
            raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert files to text.")
    parser.add_argument(
        "--mode",
        choices=BaseParser.PARSERS,        
        help="Must be supported mode. Must match the expected type of file being used, else an error will be returned.",
    )

    parser.add_argument(
        "--file",        
        help="Path to file to be converted to text. Note, if the mode and mimetype of the document submitted does not match one of those supported by file2txt, an error will be returned",
        required=True,
    )

    parser.add_argument(
        "--output",        
        help="Path to write the output markdown to, default `{input_filename}.file2txt-{mode}.md`",
    )
    parser.add_argument(
        "--extract_text_from_image",
        default=True,
        help="(optional, boolean): if images should be converted to text using OCR. Default is true.",
        type=str_to_bool
    )
    parser.add_argument(
        "--defang",
        default=True,
        help="(optional, boolean): if output should be defanged. Default is true.",
        type=str_to_bool
    )
    parser.add_argument(
        "--clean_with_openai",
        default=False,
        help="(optional, boolean): if output should be cleaned with open ai. Default is false.",
        type=str_to_bool,
    )
    return parser.parse_args()

if __name__ == "__main__":
    dotenv.load_dotenv()
    # setup logging:
    log_file = Path(f"logs/file2txt_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S_%f')}.log")
    if not isdir(log_file.parent):
        log_file.parent.mkdir()
    FORMAT = '%(asctime)s %(levelname)s %(message)s'

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logging.basicConfig(filename=log_file, encoding='utf-8', level=logging.DEBUG, format=FORMAT)
    handler.setFormatter(logging.Formatter(FORMAT))
    logging.root.addHandler(handler)
    logging.info("writing logs to %s", log_file.absolute())

    args = parse_arguments()
    md_cleaner = None
    input_file = Path(args.file)
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = input_file.with_name("{}.file2txt-{}.md".format(input_file.stem, args.mode))
    keyfile = os.path.abspath(os.path.join(os.curdir, 'keys/key.json'))
    if args.clean_with_openai:
        md_cleaner = OpenAIMDCleaner()
    try:
        logging.debug("got args: %s", " ".join(map(repr, sys.argv)))
        logging.debug("got args: %s", json.dumps(sys.argv[1:]))
        output = convert_file(args.mode, input_file, keyfile, process_raw_image_urls=args.extract_text_from_image, defang=args.defang, md_cleaner=md_cleaner)
        logging.info("conversion successful")
        output_file.write_text(BaseParser.PAGE_SEPARATOR.join(output))
        logging.info(f"wrote output to {output_file}")
    except Exception as e:
        logging.error(f"ran into an exception while parsing: %s.", e)
        logging.error("see %s for more info", log_file.absolute())
        logging.debug("%s", e, exc_info=True)
        sys.exit(135)
    
