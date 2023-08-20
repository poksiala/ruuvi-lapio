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

import json
from concurrent.futures import Future
import asyncio
from aiohttp import ClientSession, TCPConnector
from typing import Callable, Dict, List


async def handle_queue(
    args: argparse.Namespace,
    queue,
    future: Future,
    verify_ssl=True,
    api_key: str | None = None,
):
    async def send_post(session, update_data, headers: Dict[str, str]):
        async with session.post(
            args.dest,
            data=json.dumps(update_data),
            headers=headers,
        ) as response:
            logging.debug("Server responded: %s", response.status)
            body = await response.text()
            if response.status != 201:
                logging.warning("%s: %s", response.status, body)

    headers = {"content-type": "application/json"}
    if api_key:
        headers["X-API-KEY"] = api_key

    connector = TCPConnector(verify_ssl=verify_ssl)
    async with ClientSession(connector=connector) as session:
        tasks: List[asyncio.Task] = []
        while future.running():
            if not queue.empty():
                data = queue.get()
                tasks.append(asyncio.create_task(send_post(session, data, headers)))
            else:
                await asyncio.sleep(0.1)
            tasks = [task for task in tasks if not task.done()]
        for task in tasks:
            task.cancel()


def format_data(data: dict) -> dict:
    keys_with_decimals = (
        "humidity",
        "temperature",
        "pressure",
        "acceleration",
    )
    keys_as_is = (
        "battery",
        "measurement_sequence_number",
        "movement_counter",
        "tx_power",
        "acceleration_x",
        "acceleration_y",
        "acceleration_z",
    )
    res = {}
    for key in keys_with_decimals:
        res[key] = int(data[key] * 100)  # precise enough
    for key in keys_as_is:
        res[key] = int(data[key])  # ensure int
    res["mac"] = data["mac"]
    return res


def run_get_datas_background(queue, sensor_reader: Callable):
    def handle_new_data(new_data):
        sensor_data = new_data[1]
        formatted_data = format_data(sensor_data)
        logging.debug("Formatted data: %s", format_data)
        queue.put(formatted_data)

    sensor_reader(handle_new_data)
