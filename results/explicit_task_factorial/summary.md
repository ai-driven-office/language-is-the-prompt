# Explicit Task Factorial Results

## Aggregate Conditions

- `ff_0000`: `9/48 = 18.8%` (95% Wilson CI `10.2%` to `31.9%`).
- `ff_0011`: `31/48 = 64.6%` (95% Wilson CI `50.4%` to `76.6%`).
- `ff_0101`: `21/48 = 43.8%` (95% Wilson CI `30.7%` to `57.7%`).
- `ff_0110`: `38/48 = 79.2%` (95% Wilson CI `65.7%` to `88.3%`).
- `ff_1001`: `12/48 = 25.0%` (95% Wilson CI `14.9%` to `38.8%`).
- `ff_1010`: `32/48 = 66.7%` (95% Wilson CI `52.5%` to `78.3%`).
- `ff_1100`: `27/48 = 56.2%` (95% Wilson CI `42.3%` to `69.3%`).
- `ff_1111`: `37/48 = 77.1%` (95% Wilson CI `63.5%` to `86.7%`).

## Main Effects (All Languages)

- `docs_rich`: matched mean delta `0.047`, wins `7` vs losses `4`, ties `5`, exact sign p `0.548828`, Holm-adjusted p `1.0`.
- `examples`: matched mean delta `0.203`, wins `10` vs losses `2`, ties `4`, exact sign p `0.038574`, Holm-adjusted p `0.115722`.
- `contracts_explicit`: matched mean delta `0.359`, wins `13` vs losses `2`, ties `1`, exact sign p `0.007385`, Holm-adjusted p `0.02954`.
- `state_guidance`: matched mean delta `-0.026`, wins `5` vs losses `3`, ties `8`, exact sign p `0.726562`, Holm-adjusted p `1.0`.

## Main Effects By Language

- `elixir / docs_rich`: matched mean delta `0.062`, wins `7` vs losses `3`, ties `6`, exact sign p `0.34375`, Holm-adjusted p `1.0`.
- `python / docs_rich`: matched mean delta `0.031`, wins `4` vs losses `2`, ties `10`, exact sign p `0.6875`, Holm-adjusted p `1.0`.
- `typescript / docs_rich`: matched mean delta `0.047`, wins `4` vs losses `2`, ties `10`, exact sign p `0.6875`, Holm-adjusted p `0.867186`.
- `elixir / examples`: matched mean delta `0.281`, wins `9` vs losses `2`, ties `5`, exact sign p `0.06543`, Holm-adjusted p `0.26172`.
- `python / examples`: matched mean delta `0.219`, wins `9` vs losses `1`, ties `6`, exact sign p `0.021484`, Holm-adjusted p `0.064452`.
- `typescript / examples`: matched mean delta `0.109`, wins `6` vs losses `2`, ties `8`, exact sign p `0.289062`, Holm-adjusted p `0.867186`.
- `elixir / contracts_explicit`: matched mean delta `0.156`, wins `7` vs losses `5`, ties `4`, exact sign p `0.774414`, Holm-adjusted p `1.0`.
- `python / contracts_explicit`: matched mean delta `0.469`, wins `13` vs losses `0`, ties `3`, exact sign p `0.000244`, Holm-adjusted p `0.000976`.
- `typescript / contracts_explicit`: matched mean delta `0.453`, wins `11` vs losses `0`, ties `5`, exact sign p `0.000977`, Holm-adjusted p `0.003908`.
- `elixir / state_guidance`: matched mean delta `0.0`, wins `5` vs losses `4`, ties `7`, exact sign p `1.0`, Holm-adjusted p `1.0`.
- `python / state_guidance`: matched mean delta `-0.031`, wins `3` vs losses `3`, ties `10`, exact sign p `1.0`, Holm-adjusted p `1.0`.
- `typescript / state_guidance`: matched mean delta `-0.047`, wins `1` vs losses `4`, ties `11`, exact sign p `0.375`, Holm-adjusted p `0.867186`.

## Aliased Two-Factor Contrasts

- `docs_rich*examples == contracts_explicit*state_guidance`: matched mean delta `0.005`, wins `10` vs losses `9`, exact sign p `1.0`.
- `docs_rich*contracts_explicit == examples*state_guidance`: matched mean delta `-0.047`, wins `7` vs losses `14`, exact sign p `0.189247`.
- `docs_rich*state_guidance == examples*contracts_explicit`: matched mean delta `-0.078`, wins `9` vs losses `18`, exact sign p `0.122078`.

## Language By Condition

- `elixir / ff_0000`: `3/16 = 18.8%`.
- `elixir / ff_0011`: `7/16 = 43.8%`.
- `elixir / ff_0101`: `7/16 = 43.8%`.
- `elixir / ff_0110`: `10/16 = 62.5%`.
- `elixir / ff_1001`: `4/16 = 25.0%`.
- `elixir / ff_1010`: `6/16 = 37.5%`.
- `elixir / ff_1100`: `10/16 = 62.5%`.
- `elixir / ff_1111`: `11/16 = 68.8%`.
- `python / ff_0000`: `2/16 = 12.5%`.
- `python / ff_0011`: `12/16 = 75.0%`.
- `python / ff_0101`: `8/16 = 50.0%`.
- `python / ff_0110`: `14/16 = 87.5%`.
- `python / ff_1001`: `3/16 = 18.8%`.
- `python / ff_1010`: `13/16 = 81.2%`.
- `python / ff_1100`: `9/16 = 56.2%`.
- `python / ff_1111`: `13/16 = 81.2%`.
- `typescript / ff_0000`: `4/16 = 25.0%`.
- `typescript / ff_0011`: `12/16 = 75.0%`.
- `typescript / ff_0101`: `6/16 = 37.5%`.
- `typescript / ff_0110`: `14/16 = 87.5%`.
- `typescript / ff_1001`: `5/16 = 31.2%`.
- `typescript / ff_1010`: `13/16 = 81.2%`.
- `typescript / ff_1100`: `8/16 = 50.0%`.
- `typescript / ff_1111`: `13/16 = 81.2%`.
