import os
from typing import Iterator

import pytest
from ndspy import fnt, lz10, narc, rom

from zed import common, zmb

PH_ROM_PATH = os.environ.get("PH_ROM_PATH")


def _get_zmb_files() -> Iterator[tuple[str, bytes]]:
    ph_rom = rom.NintendoDSRom.fromFile(PH_ROM_PATH)
    map_folder: fnt.Folder = ph_rom.filenames["Map"]
    for map_name, folder in map_folder.folders:
        for narc_filename in folder.files:
            if not narc_filename.startswith("map"):
                continue
            narc_filepath = f"Map/{map_name}/{narc_filename}"
            narc_file = narc.NARC(lz10.decompress(ph_rom.getFileByName(narc_filepath)))
            zmb_path = f"zmb/{map_name}_{narc_filename[3:5]}.zmb"
            yield f"{narc_filepath}/{zmb_path}", narc_file.getFileByName(zmb_path)


@pytest.mark.skipif(PH_ROM_PATH is None, reason='No rom path provided')
@pytest.mark.parametrize(
    argnames="zmb_data",
    argvalues=[z[1] for z in _get_zmb_files()] if PH_ROM_PATH else [],
    ids=[z[0] for z in _get_zmb_files()] if PH_ROM_PATH else [],
)
def test_zmb(zmb_data):
    """Test ZMB module by loading a zmb file from binary data, saving it, and comparing the result to the original."""
    zmb_file = zmb.ZMB(game=common.Game.PhantomHourglass, data=zmb_data)
    assert zmb_file.save(game=common.Game.PhantomHourglass) == zmb_data
