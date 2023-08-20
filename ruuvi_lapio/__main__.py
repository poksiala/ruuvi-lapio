"""
Copyright (c) 2022, Panu Oksiala

Derived from ruuvitag_sensor example by Tomi Tuhkanen.
https://github.com/ttu/ruuvitag-sensor/blob/master/examples/send_updated_async.py

MIT License

Copyright (c) 2016 Tomi Tuhkanen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import logging

from multiprocessing import Manager
from concurrent.futures import ProcessPoolExecutor
import asyncio


from ruuvitag_sensor.ruuvi import RuuviTagSensor

from .mock_sensor import MockSensorReader

from .main import handle_queue, run_get_datas_background


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ruuvi-lapio",
        description="A simple app that sends sensory data over http",
    )
    parser.add_argument(
        "dest",
        help="Where to send measurements including protocol and path.",
    )
    parser.add_argument("--debug", action="store_true", help="Debug logging")
    parser.add_argument("--mock", action="store_true", help="Mock data")
    parser.add_argument("--insecure", action="store_true", help="Skip TLS verification")
    parser.add_argument("--api-key", help="API key for the server")
    args = parser.parse_args()
    log_level = logging.INFO if not args.debug else logging.DEBUG
    logging.basicConfig(level=log_level)
    m = Manager()
    q = m.Queue()

    executor = ProcessPoolExecutor()

    senseor_reader = (
        MockSensorReader(count=3).get_data if args.mock else RuuviTagSensor.get_data
    )
    bt_future = executor.submit(run_get_datas_background, q, senseor_reader)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        handle_queue(
            args, q, bt_future, verify_ssl=not args.insecure, api_key=args.api_key
        )
    )
    logging.info("Eventloop terminated")
    bt_future.cancel()
    executor.shutdown()
    logging.info("Process shutdown")
