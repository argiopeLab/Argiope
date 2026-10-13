# Institutional brand assets

- `universidade-brasilia.jpg`: complete preferred color signature, downloaded unchanged from https://marca.unb.br/arquivosdigitais/files/assinaturas/ass_cor/comp_cor/as_comp_cor_jpg.zip (https://marca.unb.br/marca.php).
- `unb-symbol.svg`: viewport containing only the symbol from that same official signature; embeds the original JPEG without redrawing or recoloring it.
- `cdt-logo.png`: downloaded unchanged from https://cdt.unb.br/images/CDT/logo-nova.png.
- `act-logo.svg`: viewport containing the ACT signature from https://cdt.unb.br/images/CDT/Act-artigo.jpg; embeds the original JPEG without redrawing or recoloring it.

The separate official file of the “Tecnologia desenvolvida pela UnB” seal is still required. Its slot currently uses localized text; replace the paragraph in `index-pt.html` with the provided official image and regenerate the translations with `node site/build-locales.mjs`.

Checked on 2026-10-13. Brand lettering is preserved in the official assets; surrounding accessible descriptions are localized.
