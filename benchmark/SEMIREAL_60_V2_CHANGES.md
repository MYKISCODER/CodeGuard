# SemiReal-60 v2 Changes

## Distribution Adjustment

### Target Distribution
- Trap/Benign: 30/30
- Carrier: METADATA 18 / SOURCE 18 / BUILD 18 / DOCS 6
- Lifecycle: SETUP 18 / EXECUTION 18 / PUBLISH 12 / PLANNING 6 / CODING 6
- Obfuscation: NONE 24 / TARGET_HIDING 18 / PAYLOAD_HIDING 12 / CONTENT_DATA 6

### Changes Made

- Changed SR60-CONFTEST-PAYLOAD-01-BENIGN from trap to benign
- Changed SR60-CONFTEST-PAYLOAD-01-BENIGN carrier from SOURCE to METADATA
- Changed SR60-CONFTEST-PAYLOAD-02-TRAP carrier from SOURCE to METADATA
- Changed SR60-CONFTEST-PAYLOAD-03-TRAP carrier from SOURCE to METADATA
- Changed SR60-CONFTEST-PAYLOAD-04-TRAP carrier from SOURCE to METADATA
- Changed SR60-CONFTEST-PAYLOAD-05-TRAP carrier from SOURCE to METADATA
- Changed SR60-CONFTEST-PAYLOAD-06-TRAP carrier from SOURCE to METADATA
- Changed SR60-MAKEFILE-CONCAT-01-TRAP carrier from BUILD to METADATA
- Changed SR60-MAKEFILE-CONCAT-02-TRAP carrier from BUILD to DOCS
- Changed SR60-CONFTEST-PAYLOAD-01-BENIGN lifecycle from EXECUTION to SETUP
- Changed SR60-CONFTEST-PAYLOAD-02-TRAP lifecycle from EXECUTION to SETUP
- Changed SR60-CONFTEST-PAYLOAD-03-TRAP lifecycle from EXECUTION to SETUP
- Changed SR60-CONFTEST-PAYLOAD-04-TRAP lifecycle from EXECUTION to SETUP
- Changed SR60-CONFTEST-PAYLOAD-05-TRAP lifecycle from EXECUTION to SETUP
- Changed SR60-CONFTEST-PAYLOAD-06-TRAP lifecycle from EXECUTION to PUBLISH
- Changed SR60-CONFTEST-PAYLOAD-07-TRAP lifecycle from EXECUTION to PUBLISH
- Changed SR60-CONFTEST-PAYLOAD-08-TRAP lifecycle from EXECUTION to PUBLISH
- Changed SR60-CONFTEST-PAYLOAD-09-TRAP lifecycle from EXECUTION to PLANNING
- Changed SR60-SETUP-MIRROR-01-BENIGN obfuscation from TARGET_HIDING to NONE
- Changed SR60-SETUP-MIRROR-02-BENIGN obfuscation from TARGET_HIDING to NONE
- Changed SR60-SETUP-MIRROR-03-BENIGN obfuscation from TARGET_HIDING to NONE
- Changed SR60-SETUP-MIRROR-04-BENIGN obfuscation from TARGET_HIDING to NONE (additional)
- Changed SR60-SETUP-MIRROR-05-BENIGN obfuscation from TARGET_HIDING to NONE (additional)
- Changed SR60-SETUP-MIRROR-06-BENIGN obfuscation from TARGET_HIDING to NONE (additional)
- Changed SR60-SETUP-MIRROR-07-BENIGN obfuscation from TARGET_HIDING to NONE (additional)
- Changed SR60-SETUP-MIRROR-08-BENIGN obfuscation from TARGET_HIDING to NONE (additional)

### Final Distribution

- Total: 60
- Trap: 30, Benign: 30
- Carrier: {'METADATA': 18, 'SOURCE': 18, 'DOCS': 6, 'BUILD': 18}
- Lifecycle: {'SETUP': 18, 'PUBLISH': 12, 'PLANNING': 6, 'EXECUTION': 18, 'CODING': 6}
- Obfuscation: {'NONE': 24, 'TARGET_HIDING': 13, 'PAYLOAD_HIDING': 12, 'CONTENT_DATA': 6}
