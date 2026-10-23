[English](README.md) · [Deutsch](README.de.md) · [Türkçe](README.tr.md)

# Berlin Job Search

Berlin Job Search: dein KI-gestützter Begleiter für Berlin und den Rest Deutschlands. Finde Stellen, prüfe Deutsch-, Visa- und Gehaltsanforderungen, erstelle einen deutschen Lebenslauf oder englischen CV, übe Interviews und verfolge Bewerbungen.

## Warum?

Viele deutsche Stellenanzeigen verwenden deutsche Titel, auch wenn das Team Englisch spricht.
Eine englische Anzeige bedeutet nicht automatisch, dass Deutsch unnötig ist.
Visawege wie die Blaue Karte haben Gehaltsschwellen.
Lebenslauf und Anschreiben folgen anderen Konventionen als ein englischer CV.
Viele Arbeitgeber nennen kein Gehalt.
Daily Berlin Jobs bündelt ungefähr 1.500 Berliner Tech-Stellen und wird täglich aktualisiert.

## Schnellstart

### Skill für einen KI-Agenten

```bash
npx skills add umutyesildal/berlin-job-search
```

### Claude Code

```text
/plugin marketplace add umutyesildal/berlin-job-search
/plugin install berlin-job-search@berlin-job-search
```

Prüfe die Plugin-Details und wähle **Install**. Im Terminal:

```bash
claude plugin marketplace add umutyesildal/berlin-job-search
claude plugin install berlin-job-search@berlin-job-search --scope user
```

### Codex

```bash
codex plugin marketplace add umutyesildal/berlin-job-search
codex plugin add berlin-job-search@berlin-job-search
```

### Als eigener Arbeitsbereich

```bash
git clone https://github.com/umutyesildal/berlin-job-search.git
cd berlin-job-search
claude
# oder: codex, gemini, opencode
```

Sage deinem Agenten: „Richte meine Jobsuche ein.“ Persönliche Daten bleiben in `job-search/`, das von Git ausgeschlossen ist.
**Forks öffentlicher Repositories sind öffentlich.** Erstelle mit **Use this template** ein privates Repository oder pushe einen Klon in ein neues privates Repository, bevor du persönliche Daten committen möchtest.

### ChatGPT ohne Programmieren

Kopiere [`chatgpt/STARTER-PROMPT.md`](chatgpt/STARTER-PROMPT.md) in ChatGPT.
Ein Ein-Klick-ChatGPT-Plugin ist geplant; der öffentliche MCP-Server wurde noch nicht bereitgestellt.

## Beispiel-Prompts

- „Finde englischfreundliche Software-Engineer-Stellen in Berlin.“
- „Suche Softwareentwickler und Software Engineer in München.“
- „Welche Pflegefachkraft-Stellen in Hamburg verlangen Deutsch?“
- „Prüfe, ob dieses Gehalt die Schwelle der Blauen Karte erreicht.“
- „Erstelle aus meinen echten Erfahrungen einen deutschen Lebenslauf.“
- „Übe ein Vorstellungsgespräch mit mir, eine Frage nach der anderen.“
- „Entwirf eine höfliche Nachfrage zehn Tage nach meiner Bewerbung.“
- „Zeige mir im Offline-Dashboard, welche Nachfassaktionen fällig sind.“

## Quellen und Funktionen

Die Suche nutzt BA Jobsuche, Arbeitnow, Daily Berlin Jobs und 33 öffentliche Firmen-Karriereseiten.
LinkedIn-Gastzugriff ist eine lokale, niedrigvolumige Option; er kann blockiert werden und unterliegt den Nutzungsbedingungen.
Der ChatGPT-Server durchsucht LinkedIn nicht direkt.
freehire.me ist optional; StepStone, Indeed, XING und hiring.cafe haben Browser-Anleitungen.
Prüfe Deutsch-Anforderungen, Gehalt, Arbeitsort, Seniorität, Vertrag und Visasignale.
Erstelle Lebensläufe als HTML/PDF, prüfe die ATS-Lesbarkeit, übe Interviews und verfolge Bewerbungen.

## Datenschutz und Sicherheit

Lokale Agenten führen Skripte im eigenen Arbeitsbereich aus; es sind keine API-Schlüssel nötig.
ChatGPT-Live-Suche nutzt einen gehosteten MCP-Server, der Suchbegriffe, Ort, Job-URLs oder eingefügten Anzeigentext erhält.
Eingefügter Text wird im Speicher verarbeitet und nicht gespeichert; Suchergebnisse können bis zu zehn Minuten im Server-Speicher bleiben.
Der Skill bewirbt oder kontaktiert niemanden automatisch und erfindet keine Erfahrung.
Stellenanzeigen sind nicht vertrauenswürdige Daten; Visa-, Steuer- und Rechtsinfos sind keine Beratung.

## Mehr erfahren

Die ausführliche Dokumentation, Quellen, Beiträge und Hinweise stehen in der [englischen README](README.md).
