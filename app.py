# -*- coding: utf-8 -*-
"""
app.py — entry point.

Run with:  streamlit run app.py

This file deliberately stays thin. The application itself lives under app/:

    app/core/       config, db, session, billing, email, analytics
    app/features/   interview, jobs, resume, feedback
    app/ui/         theme, auth views
    app/demos/      public no-login demos
"""

import os
import sys

# Make `app.*` importable no matter where streamlit is launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The real application. (Still one large module — see docs/ARCHITECTURE.md for
# the plan to split it. Moving it behind this entry point is step one.)
import app._legacy_main  # noqa: F401,E402
