# Third-Party Visualization Notices

CodeRisk / PICAS original code and documentation: Copyright (c) 2026 魏语石 (weidonglang), MIT.

The new statistical view imports selected Apache ECharts modules. Third-party ownership and licenses are retained; the project MIT statement does not relicense these packages.

| Package | Version | License | Source |
| --- | --- | --- | --- |
| Apache ECharts | 6.1.0 (pinned) | Apache-2.0 | <https://github.com/apache/echarts> |
| zrender | See package-lock.json | BSD-3-Clause | <https://github.com/ecomfe/zrender> |
| tslib | See package-lock.json | 0BSD | <https://github.com/microsoft/tslib> |

These are npm packages, not vendored dataset code. Their complete license/NOTICE files are supplied in the installed packages. Existing Vue, Element Plus and other dependencies retain their own licenses. Installation does not grant rights to student code or externally collected datasets.

The statistical view uses ECharts only for rendering descriptive values in the browser. It does not send code or scores to ECharts, a CDN, or a model service at runtime.
