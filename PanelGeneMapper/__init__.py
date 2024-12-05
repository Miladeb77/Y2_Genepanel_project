# PanelGeneMapper/modules/__init__.py

# Expose specific functions or modules for easier imports
from .build_panelApp_database import main as build_panelApp_database
from .build_patient_database import main as build_patient_database
from .retrieve_data import main as retrieve_data_main
from .settings import run_update_check

# License information (if desired, as shown in the example)
"""
<LICENSE>
Copyright (C) 2024 PanelGeneMapper Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
</LICENSE>
"""
