"""CSV-Import und Kennzahlenberechnung mit der Python-Standardbibliothek."""

import csv
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Kennzahlen:
    gesamtrendite: float
    annualisierte_volatilitaet: float
    maximaler_drawdown: float


def lese_schlusskurse(datei: str | Path) -> list[float]:
    """Liest Schlusskurse einer CSV mit Datum- und Schluss-Spalten."""
    kurse: list[tuple[date, float]] = []
    with open(datei, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "Datum" not in reader.fieldnames or "Schluss" not in reader.fieldnames:
            raise ValueError("CSV muss die Spalten 'Datum' und 'Schluss' enthalten")
        for row in reader:
            nummer = reader.line_num
            datum_text = (row.get("Datum") or "").strip()
            kurs_text = (row.get("Schluss") or "").strip()
            if not datum_text or not kurs_text:
                raise ValueError(f"Fehlender Wert in CSV-Zeile {nummer}")
            try:
                datum = date.fromisoformat(datum_text)
                kurs = float(kurs_text)
            except ValueError as exc:
                raise ValueError(f"Ungültiger Wert in CSV-Zeile {nummer}") from exc
            if not math.isfinite(kurs) or kurs <= 0:
                raise ValueError(f"Schlusskurs muss positiv und endlich sein (Zeile {nummer})")
            kurse.append((datum, kurs))
    kurse.sort(key=lambda item: item[0])
    return [kurs for _, kurs in kurse]


def berechne_kennzahlen(kurse: Iterable[float]) -> Kennzahlen:
    """Berechnet Gesamtrendite, annualisierte Populationsvolatilität und Drawdown."""
    werte = list(kurse)
    if any(not math.isfinite(k) or k <= 0 for k in werte):
        raise ValueError("Schlusskurse müssen positiv und endlich sein")
    if len(werte) < 1:
        raise ValueError("Mindestens ein Schlusskurs ist erforderlich")
    try:
        renditen = [aktuell / vorher - 1 for vorher, aktuell in zip(werte, werte[1:])]
        gesamtrendite = werte[-1] / werte[0] - 1
        if renditen:
            mittelwert = sum(renditen) / len(renditen)
            varianz = sum((r - mittelwert) ** 2 for r in renditen) / len(renditen)
            volatilitaet = math.sqrt(varianz * 252)
        else:
            volatilitaet = 0.0
        hoch = werte[0]
        drawdown = 0.0
        for kurs in werte:
            hoch = max(hoch, kurs)
            drawdown = min(drawdown, kurs / hoch - 1)
        result = Kennzahlen(gesamtrendite, volatilitaet, drawdown)
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("Schlusskurse verursachen einen numerischen Überlauf") from exc
    if not all(math.isfinite(value) for value in (
        result.gesamtrendite, result.annualisierte_volatilitaet, result.maximaler_drawdown
    )):
        raise ValueError("Schlusskurse verursachen nicht-endliche Kennzahlen")
    return result
