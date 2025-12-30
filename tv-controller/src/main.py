#!/usr/bin/env python3

import logging
import importlib
from enum import Enum
from typing import Annotated
from fastapi import FastAPI, Query, HTTPException
import time

from config import TVs

# Import LOG_LEVEL if available, otherwise default to INFO
try:
    from config import LOG_LEVEL
except ImportError:
    LOG_LEVEL = "INFO"

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if "all" in TVs:
    raise ValueError(
        "Cannot configure a TV with ID 'all' - reserved for broadcast commands. Fix config.py"
    )


def create_tv_controller(config: dict):
    """
    Dynamically import and instantiate a TV controller based on config.

    Args:
        config: TV configuration dict containing 'protocol_class' key

    Returns:
        Instance of a BaseTVController subclass

    Example config:
        {
            "name": "Top TV",
            "port": "/dev/ttyUSB0",
            "protocol_class": "sony_bravia_serial.SonyBraviaSerial"
        }
    """
    # Default to Sony Bravia Serial protocol if not specified
    protocol_class_path = config.get("protocol_class", "sony_bravia_serial.SonyBraviaSerial")

    # Split into module and class name
    module_name, class_name = protocol_class_path.rsplit(".", 1)

    # Dynamically import the module and get the class
    module = importlib.import_module(module_name)
    controller_class = getattr(module, class_name)

    # Instantiate and return
    logger.info(f"Creating TV controller using {protocol_class_path}")
    return controller_class(config)


TVId = Enum("TVId", {tv_id: tv_id for tv_id in TVs.keys()})
AllTVId = Enum("AllTVId", {**{tv_id: tv_id for tv_id in TVs.keys()}, "all": "all"})
tvs = {tv_id: create_tv_controller(cfg) for tv_id, cfg in TVs.items()}

app = FastAPI()


def _get_tvs(tv_id: AllTVId):
    if tv_id.value == "all":
        return [(id, tv) for id, tv in tvs.items()]
    else:
        return [(tv_id.value, tvs[tv_id.value])]


@app.get("/healthcheck")
def healthcheck():
    return {
        "message": "Hello it's me, TV controller, I am quite well thank you",
        "status": "ok",
    }


@app.post("/tv/{tv_id}/power/on")
def power_on(tv_id: AllTVId):
    results = {}
    for tv_id_str, tv in _get_tvs(tv_id):
        try:
            tv.power_on()
            results[tv_id_str] = "ok"
        except Exception as e:
            results[tv_id_str] = f"error: {e}"

    return {"status": results}


@app.post("/tv/{tv_id}/power/off")
def power_off(tv_id: AllTVId):
    results = {}
    for tv_id_str, tv in _get_tvs(tv_id):
        try:
            tv.power_off()
            results[tv_id_str] = "ok"
        except Exception as e:
            results[tv_id_str] = f"error: {e}"

    return {"status": results}


@app.post("/tv/{tv_id}/standby/on")
def standby_on(tv_id: AllTVId):
    results = {}
    for tv_id_str, tv in _get_tvs(tv_id):
        try:
            tv.standby_on()
            results[tv_id_str] = "ok"
        except Exception as e:
            results[tv_id_str] = f"error: {e}"

    return {"status": results}


@app.post("/tv/{tv_id}/standby/off")
def standby_off(tv_id: AllTVId):
    results = {}
    for tv_id_str, tv in _get_tvs(tv_id):
        try:
            tv.standby_off()
            results[tv_id_str] = "ok"
        except Exception as e:
            results[tv_id_str] = f"error: {e}"

    return {"status": results}


@app.post("/tv/{tv_id}/power/toggle")
def toggle_power(tv_id: AllTVId):
    results = {}
    for tv_id_str, tv in _get_tvs(tv_id):
        try:
            tv.toggle_power()
            results[tv_id_str] = "ok"
        except Exception as e:
            results[tv_id_str] = f"error: {e}"

    return {"status": results}


@app.post("/tv/{tv_id}/volume/up")
def volume_up(
    tv_id: AllTVId,
    step: Annotated[
        int,
        Query(description="Amount of volume to increment by", ge=1),
    ] = 1,
):
    results = {}
    for tv_id_str, tv in _get_tvs(tv_id):
        try:
            for _ in range(step):
                tv.volume_up()
                if step > 1:
                    time.sleep(0.1)

            results[tv_id_str] = "ok"
        except Exception as e:
            results[tv_id_str] = f"error: {e}"

    return {"status": results}


@app.post("/tv/{tv_id}/volume/down")
def volume_down(
    tv_id: AllTVId,
    step: Annotated[
        int,
        Query(description="Amount of volume to decrement by", ge=1),
    ] = 1,
):
    results = {}
    for tv_id_str, tv in _get_tvs(tv_id):
        try:
            for _ in range(step):
                tv.volume_down()
                if step > 1:
                    time.sleep(0.1)
            results[tv_id_str] = "ok"
        except Exception as e:
            results[tv_id_str] = f"error: {e}"

    return {"status": results}


@app.post("/tv/{tv_id}/volume/mute/toggle")
def toggle_mute(tv_id: AllTVId):
    results = {}
    for tv_id_str, tv in _get_tvs(tv_id):
        try:
            tv.toggle_mute()
            results[tv_id_str] = "ok"
        except Exception as e:
            results[tv_id_str] = f"error: {e}"

    return {"status": results}


@app.get("/tv/{tv_id}/power")
def get_power_state(tv_id: TVId):
    try:
        tv = tvs[tv_id.value]
        power_state = tv.get_power_state()
        power_str = "on" if power_state == tv.POWER_ON_DATA else "off"
        return {"tv_id": tv_id.value, "power": power_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
