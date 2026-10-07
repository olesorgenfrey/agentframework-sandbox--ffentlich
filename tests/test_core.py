import math

import pytest

from kennzahlen import berechne_kennzahlen, lese_schlusskurse


def test_csv_liest_kurse_sortiert_nach_datum(tmp_path):
    p = tmp_path / "kurse.csv"
    p.write_text("Datum,Schluss\n2024-01-02,110\n2024-01-01,100\n", encoding="utf-8")
    assert lese_schlusskurse(p) == [100.0, 110.0]


def test_leere_datei_hat_keine_erforderlichen_spalten(tmp_path):
    p = tmp_path / "leer.csv"
    p.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Spalten"):
        lese_schlusskurse(p)


def test_einzelner_kurs_liefert_null_volatilitaet_und_drawdown():
    result = berechne_kennzahlen([100])
    assert result.gesamtrendite == 0
    assert result.annualisierte_volatilitaet == 0
    assert result.maximaler_drawdown == 0


def test_gesamtrendite_und_volatilitaet_sind_handrechenbar():
    # Tagesrenditen 10 % und -9,0909... %, Mittelwert 0,4545... %.
    result = berechne_kennzahlen([100, 110, 100])
    r1, r2 = 0.1, 100 / 110 - 1
    avg = (r1 + r2) / 2
    expected_vol = math.sqrt(((r1 - avg) ** 2 + (r2 - avg) ** 2) / 2 * 252)
    assert result.gesamtrendite == pytest.approx(0)
    assert result.annualisierte_volatilitaet == pytest.approx(expected_vol)
    assert result.maximaler_drawdown == pytest.approx(-1 / 11)


def test_fehlender_csv_wert_wird_abgelehnt(tmp_path):
    p = tmp_path / "luecke.csv"
    p.write_text("Datum,Schluss\n2024-01-01,100\n2024-01-02,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Fehlender Wert"):
        lese_schlusskurse(p)


def test_leere_kursliste_wird_abgelehnt():
    with pytest.raises(ValueError, match="Mindestens ein"):
        berechne_kennzahlen([])
