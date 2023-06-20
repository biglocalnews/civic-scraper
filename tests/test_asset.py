import re
from unittest.mock import Mock, call, patch

import pytest

from civic_scraper.base.asset import Asset, AssetCollection

from .conftest import file_lines


def test_asset_args(asset_inputs):
    kwargs = asset_inputs[0]
    url = kwargs.pop("url")
    asset = Asset(url, **kwargs)
    assert asset.place == "nashcounty"
    assert asset.place_name == "Nash County"


@pytest.fixture
def asset_collection(asset_inputs):
    return AssetCollection([Asset(**kwargs) for kwargs in asset_inputs])


def test_asset_methods():
    # extend
    extended = AssetCollection([1, 2])
    extended.extend([3, 4])
    assert extended == AssetCollection([1, 2, 3, 4])
    # append
    appended = AssetCollection([1, 2])
    appended.append([3, 4])
    assert appended == AssetCollection([1, 2, [3, 4]])
    # indexing
    indexed = AssetCollection([1, 2])
    assert indexed[1] == 2


def test_csv_export(tmpdir, asset_collection):
    "csv_export should write standard filename to a target_dir"
    outfile = asset_collection.to_csv(target_dir=tmpdir)
    pattern = re.compile(r".+civic_scraper_assets_meta_\d{8}T\d{4}z.csv")
    assert re.match(pattern, outfile)
    contents = file_lines(outfile)
    assert len(contents) == 3
    # Check header and contents
    assert contents[0].startswith("place")
    assert contents[0].strip().endswith("content_length")
    assert "minutes" in contents[1]
    assert "2020-05-04" in contents[1]
    assert "agenda" in contents[2]


def test_asset_download(tmpdir, asset_inputs):
    response = Mock(name="MockResponse")
    response.content = b"some data"
    to_patch = "civic_scraper.base.asset.requests.get"
    with patch(to_patch) as mock_method:
        mock_method.return_value = response
        asset_objs = [Asset(**kwargs) for kwargs in asset_inputs]
        for asset in asset_objs:
            asset.download(target_dir=tmpdir)
        assert mock_method.mock_calls == [
            call(
                "http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Minutes/_05042020-381",
                allow_redirects=True,
            ),
            call(
                "http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05042020-381",
                allow_redirects=True,
            ),
        ]
        # check files written
        actual_file_names = {f.basename for f in tmpdir.listdir()}
        expected_file_names = {
            "civicplus_nc-nashcounty_05042020-381_agenda.pdf",
            "civicplus_nc-nashcounty_05042020-381_minutes.pdf",
        }
        assert actual_file_names == expected_file_names
