# COHP/COOP GUI Plotter

## Overview

The **COHP/COOP GUI Plotter** is a Python-based web application for interactive visualization of chemical bonding data from [LOBSTER](http://www.cohp.de). It supports plotting **COHP** (Crystal Orbital Hamilton Population) and **COOP** (Crystal Orbital Overlap Population) data from `COHPCAR.lobster` and `COOPCAR.lobster` files respectively. Designed with a user-friendly GUI using Plotly and Dash, it allows researchers to analyze bonding interactions, customize graph settings, and export publication-quality plots.

---

## Features

- ✅ **Upload ZIP files** containing `COHPCAR.lobster`, `COOPCAR.lobster`, and optionally `POSCAR`.
- ✅ **Interactive Plotting** of both COHP and COOP curves with toggle switches for each atomic pair.
- ✅ **Support for ICOHP and ICOOP toggling**: Show/hide integrated COHP/COOP per pair.
- ✅ **Custom X/Y Axis Ranges** for both COHP and COOP graphs.
- ✅ **Live Title & Axis Label Toggles**.
- ✅ **Legend Color Customization** for each element pair.
- ✅ **Auto-handling of file parsing**, including energy and interaction blocks.
- ✅ **High-quality PNG Export** using Plotly’s Kaleido backend.
- ✅ **Sorted legends based on Mendeleev numbers** for intuitive display.
- ✅ **Subscript formatting** for chemical formulas (e.g., `Gd10RuCd3` → `Gd₁₀RuCd₃`).

---

## Hosting

The app is live on Heroku:

🔗 [Open the COHP/COOP GUI Plotter](https://cohp-coop-gui-1de5a0643ceb.herokuapp.com)

---

## How It Works

### 1. Upload

Upload a **ZIP file** containing a folder that includes:

- `COHPCAR.lobster` (optional but recommended)
- `COOPCAR.lobster` (optional but recommended)
- `POSCAR` (used for labeling if present)

The folder **must** be named after your compound (e.g., `Gd10RuCd3`) — this name is used as the plot title.

### 2. Parsing

- The app reads bonding interactions starting with `No.1` from each file.
- Each pair like `Ge1->Ru2` is grouped into `Ge-Ru`.
- The energy grid and population values are extracted using `numpy` and `re`.

### 3. Plotting

- Two plots: **COHP** and **COOP**, rendered with Plotly.
- Each pair is plotted in a unique color with an optional ICOHP/ICOOP overlay.
- Axis ranges and labels can be modified live.

### 4. Customization

- Adjust axis limits for both COHP and COOP independently.
- Toggle individual pairs or ICOHP/ICOOP contributions.
- Toggle plot title, axis titles, and scale indicators.
- Export graphs to PNG with one click.

---

## Installing locally

### Prerequisites

- Python ≥ 3.10
- `conda` environment recommended

### 1. Clone Repository

```bash
git clone https://github.com/emiljaffal/cohp-coop-gui
cd cohp-coop-gui
```

### 2. Install Dependencies

```bash
conda install --file requirements.txt
```
or
```bash
pip install -r requirements.txt
```

### 3. Launch App

```bash
python app.py
```

### 4. Access in Browser

Navigate to [http://127.0.0.1:8050](http://127.0.0.1:8050)

---

## Example

**Folder Structure (Before ZIP):**
```
Gd10RuCd3/
├── COHPCAR.lobster
├── COOPCAR.lobster
```
ZIP this folder (not the contents directly) and upload to the web app.

---

## Output

- Two side-by-side interactive plots.
- High-resolution PNG downloads for COHP and COOP.
- Plot title: Gd₁₀RuCd₃ COHP or COOP.

---

## Future Features

🚧 Planned improvements include:

- Support for spin-resolved COHPs.

See: [GitHub Issues](https://github.com/emiljaffal/cohp-coop-gui/issues)

---

## License

MIT License. See LICENSE for details.

---

## Contact

For questions or collaborations, open an issue or contact via GitHub:

👉 [EmilJaffal/cohp-coop-gui](https://github.com/emiljaffal/cohp-coop-gui)

---

## File Formats

### COHPCAR.lobster

- Contains the projected COHPs (pCOHPs) as requested in the `lobsterin` file.
- Format resembles TB-LMTO-ASA’s COPL file:
  - **Starting from line 3:** Labels for the interactions, followed by the actual data.
  - **Column 1:** Energy axis (Fermi level shifted to 0 eV).
  - **Column 2:** pCOHP averaged over all atom pairs specified.
  - **Column 3:** Integrated pCOHP (IpCOHP) averaged over all atom pairs.
  - **Column 4:** pCOHP of the first interaction.
  - **Column 5:** IpCOHP of the first interaction.
  - ...and so on for additional interactions.
- **Spin-polarized calculations:**  
  - The first set of columns (2, 3, …, 2N+3) is for the first (up) spin.
  - The next set (2N+4, 2N+5, …, 4N+5) is for the second (down) spin.  
  - Here, N is the number of interactions.

### COOPCAR.lobster

- Same format as `COHPCAR.lobster`, but for projected COOP (pCOOP) and its integral (IpCOOP).

---