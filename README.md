# STL jewellery weight and price calculator

A Streamlit app that turns a jewellery STL file into a metal weight and an indicative price, with an interactive 3D viewer. Built for bench and CAD work where the question is "what will this weigh in 18K, and roughly what will it cost today".

## What it does

- **Volume from the mesh.** Reads the STL (units in millimetres), computes the enclosed volume from the triangle soup, and reports bounding box, triangle count and surface statistics.
- **Weight per alloy.** Multiplies volume by the density of the chosen alloy: yellow, white and rose gold across the common karats, sterling and fine silver, platinum 950 and 900, palladium 950 and rhodium. Densities are listed in the sidebar next to each alloy with a one-line note on what the alloy is used for.
- **Live pricing.** Pulls spot prices for gold, silver, platinum and palladium (USD per ounce) and the USD to INR rate from free public feeds, applies the alloy's purity multiplier, and shows the metal value with optional making charge and GST percentages.
- **Interactive 3D viewer.** Plotly mesh render coloured by the selected metal, rotatable in the browser.
- **Ring detection and size.** Estimates whether the model is a ring from its proportions and, if so, reports an approximate inner diameter and ring size.
- **Comparison charts.** Weight and price across every alloy for the same model, so a customer can compare 14K against 18K or platinum at a glance.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

`run.sh` and `run.bat` wrap the same two steps for macOS/Linux and Windows.

## Notes

- Densities are in g/mm³ and assume a solid, watertight mesh. Hollow or open meshes will under- or over-report.
- Prices are indicative. The feeds update daily and the app caches the last fetch; check the timestamp shown in the sidebar before quoting.

MIT licence.
