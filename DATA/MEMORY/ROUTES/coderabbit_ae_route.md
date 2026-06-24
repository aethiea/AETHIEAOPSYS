# CodeRabbit AE Route

## Authority
- AUTH: operator_only
- No CodeRabbit token belongs in Git.
- No SSH key custody belongs to assistant.
- No AEVPS install runs without operator shell authority.

## AEUSB / HOSTESS
- Role: portable CodeRabbit command wrapper.
- Wrapper: `/mnt/h/AETHIEAOPSYS/TOOLIO/bin/coderabbit-ae`
- Alias: `/mnt/h/AETHIEAOPSYS/TOOLIO/bin/cr-ae`
- Host binary: `$HOME/.local/bin/coderabbit`
- Use: run reviews from the AETHIEAOPSYS Git work tree.

## AEXHD
- Role: receipt / mirror lane.
- Receipt path: `/mnt/i/AETHIEAOPSYS/DATA/MEMORY/ROUTES/coderabbit_cli_route_*.txt`
- No primary auth stored here.

## AECLOUD
- Role: route/control-plane note only.
- Cloudflare/AETHERNet may expose service lanes, but CodeRabbit CLI itself remains a shell tool.
- No CodeRabbit auth is routed through Cloudflare.

## AEVPS
- Role: always-on execution surface after operator-approved shell access.
- Future install command, run only on AEVPS by operator:
  `curl -fsSL https://cli.coderabbit.ai/install.sh | sh`
- Future verify command on AEVPS:
  `coderabbit --version || cr --version`
- Future auth command, operator only:
  `coderabbit auth login`
