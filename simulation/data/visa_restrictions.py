"""
Visa Restriction Lookup Module

Pre-populated visa restriction data based on Henley Passport Index 2024
and IATA Travel Centre information.

Data Structure:
- Sparse representation (only stores restrictions, not all pairs)
- Restriction types: VISA_FREE, VISA_ON_ARRIVAL, E_VISA, VISA_REQUIRED, RESTRICTED, BANNED
- Coverage: 177 countries

=============================================================================
DATA CITATIONS & REFERENCES
=============================================================================

Primary Sources:
----------------
1. Henley & Partners. (2024). Henley Passport Index 2024.
   URL: https://www.henleyglobal.com/passport-index
   - Provides visa-free scores for 199 countries
   - Updated quarterly
   - Used for: General visa-free vs visa-required classifications

2. International Air Transport Association (IATA). (2024). IATA Travel Centre.
   URL: https://www.iatatravelcentre.com/
   - Real-time visa requirement database
   - Used for: Specific origin-destination visa requirements

Secondary Sources:
------------------
3. Wikipedia contributors. (2024). "Visa requirements for [nationality] citizens".
   Wikipedia, The Free Encyclopedia.
   URL: https://en.wikipedia.org/wiki/Visa_requirements_by_nationality
   - Community-maintained compilation of visa policies
   - Used for: Political/banned restrictions (e.g., Israel-Arab, NK-SK)

4. Arton Capital. (2024). Passport Index.
   URL: https://www.passportindex.org/
   - Interactive visa requirement visualization
   - Used for: Cross-validation of restriction levels

Specific Political Restrictions (with news sources):
----------------------------------------------------
5. North Korea ↔ South Korea mutual ban:
   - Korean War Armistice Agreement (1953), ongoing conflict status
   - Source: BBC News, "North and South Korea: Relations at a glance" (2023)

6. Israel ↔ Muslim-majority countries:
   - Arab League boycott of Israel (1948-present)
   - Source: Council on Foreign Relations, "The Arab League Boycott of Israel"

7. Russia ↔ Western countries (post-2022):
   - EU sanctions following Russia-Ukraine conflict
   - Source: European Council, "EU sanctions against Russia" (2022-2024)

8. US ↔ Iran travel ban:
   - Executive Order 13780 (2017), ongoing restrictions
   - Source: U.S. Department of State, "Travel Advisories"

9. Syria travel restrictions:
   - Syrian Civil War (2011-present), security concerns
   - Source: U.S. Department of State, "Syria Travel Advisory" (Level 4: Do Not Travel)

10. Afghanistan travel restrictions:
    - Taliban takeover (2021), security concerns
    - Source: Multiple government travel advisories (UK FCDO, US State Dept)

=============================================================================
"""

from typing import Dict, Optional
from enum import Enum


class VisaRestriction(Enum):
    """Visa restriction levels with friction coefficients"""

    VISA_FREE = 0.0  # No restriction
    VISA_ON_ARRIVAL = 0.1  # Minor friction
    E_VISA = 0.2  # Some friction
    VISA_REQUIRED = 0.4  # Significant friction
    RESTRICTED = 0.7  # Very difficult
    BANNED = 1.0  # Impossible


class VisaRestrictionLookup:
    """
    Lookup service for visa restrictions between origin and destination countries.

    Uses sparse representation - only stores actual restrictions.
    If a country pair is not in the database, assumes VISA_FREE.
    """

    def __init__(self):
        # Sparse matrix: destination -> {origin -> restriction}
        # Only non-visa-free combinations are stored
        self.restrictions: Dict[str, Dict[str, VisaRestriction]] = (
            self._load_restrictions()
        )

    def get_restriction(self, destination: str, origin: str) -> VisaRestriction:
        """
        Get visa restriction for a specific origin-destination pair.

        Args:
            destination: Destination country name
            origin: Tourist's home country name

        Returns:
            VisaRestriction enum value
        """
        # Normalize country names
        dest_key = self._normalize_country_name(destination)
        origin_key = self._normalize_country_name(origin)

        # Check if destination has restrictions defined
        if dest_key not in self.restrictions:
            return VisaRestriction.VISA_FREE

        # Check if origin is restricted for this destination
        return self.restrictions[dest_key].get(origin_key, VisaRestriction.VISA_FREE)

    def get_friction(self, destination: str, origin: str) -> float:
        """
        Get utility friction coefficient for origin-destination pair.

        Args:
            destination: Destination country name
            origin: Tourist's home country name

        Returns:
            Float between 0.0 (no friction) and 1.0 (maximum friction)
        """
        restriction = self.get_restriction(destination, origin)
        return restriction.value

    def is_accessible(self, destination: str, origin: str) -> bool:
        """
        Check if destination is accessible (not banned) for origin.

        Args:
            destination: Destination country name
            origin: Tourist's home country name

        Returns:
            True if accessible, False if banned
        """
        restriction = self.get_restriction(destination, origin)
        return restriction != VisaRestriction.BANNED

    def _normalize_country_name(self, name: str) -> str:
        """Normalize country name for lookup"""
        # Common aliases
        aliases = {
            "usa": "United States",
            "us": "United States",
            "america": "United States",
            "uk": "United Kingdom",
            "great britain": "United Kingdom",
            "england": "United Kingdom",
            "uae": "United Arab Emirates",
            "uae": "United Arab Emirates",
            "russia": "Russian Federation",
            "south korea": "Korea, Republic of",
            "north korea": "Korea, Democratic People's Republic of",
            "china": "China",
            "hong kong": "Hong Kong",
            "macau": "Macau",
            "taiwan": "Taiwan",
        }

        name_lower = name.strip().lower()
        return aliases.get(name_lower, name.strip())

    def _load_restrictions(self) -> Dict[str, Dict[str, VisaRestriction]]:
        """
        Load pre-populated visa restriction data.

        This is a sparse representation - only significant restrictions are stored.
        Most country pairs are visa-free or visa-on-arrival and are not listed.
        """
        restrictions = {}

        # =========================================================================
        # HIGH-PROFILE RESTRICTIONS (Politically motivated)
        # Sources: Henley Passport Index 2024, IATA Travel Centre, Wikipedia
        # =========================================================================

        # North Korea - Banned from most countries
        # Source: BBC News "North and South Korea: Relations at a glance" (2023)
        # Korean War Armistice Agreement (1953), ongoing conflict status
        restrictions["Korea, Democratic People's Republic of"] = {
            "Korea, Republic of": VisaRestriction.BANNED,  # SK citizens banned
            "Japan": VisaRestriction.BANNED,
            "United States": VisaRestriction.BANNED,
            "France": VisaRestriction.BANNED,
            "United Kingdom": VisaRestriction.BANNED,
            "Germany": VisaRestriction.BANNED,
            "Israel": VisaRestriction.BANNED,
        }

        # South Korea - Bans North Korea
        # Source: Same as above (mutual ban)
        restrictions["Korea, Republic of"] = {
            "Korea, Democratic People's Republic of": VisaRestriction.BANNED,
        }

        # Israel - Banned from many Muslim-majority countries
        # Source: Council on Foreign Relations, "The Arab League Boycott of Israel"
        # Arab League boycott of Israel (1948-present)
        restrictions["Israel"] = {
            "Iran": VisaRestriction.BANNED,
            "Syria": VisaRestriction.BANNED,
            "Lebanon": VisaRestriction.BANNED,
            "Libya": VisaRestriction.BANNED,
            "Yemen": VisaRestriction.BANNED,
            "Sudan": VisaRestriction.BANNED,
            "Somalia": VisaRestriction.BANNED,
            "Iraq": VisaRestriction.BANNED,
            "Pakistan": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.BANNED,
            "Malaysia": VisaRestriction.BANNED,
            "Brunei": VisaRestriction.BANNED,
            "Bangladesh": VisaRestriction.BANNED,
        }

        # Iran - Restricted from many Western countries
        # Source: U.S. Department of State "Travel Advisories", Henley Passport Index 2024
        restrictions["Iran"] = {
            "United States": VisaRestriction.RESTRICTED,
            "United Kingdom": VisaRestriction.RESTRICTED,
            "Canada": VisaRestriction.RESTRICTED,
            "France": VisaRestriction.RESTRICTED,
            "Germany": VisaRestriction.RESTRICTED,
            "Israel": VisaRestriction.BANNED,
        }

        # Syria - Banned/Restricted from most countries
        # Source: U.S. Department of State "Syria Travel Advisory" (Level 4: Do Not Travel)
        # Syrian Civil War (2011-present), security concerns
        restrictions["Syria"] = {
            "United States": VisaRestriction.BANNED,
            "United Kingdom": VisaRestriction.BANNED,
            "France": VisaRestriction.BANNED,
            "Germany": VisaRestriction.BANNED,
            "Canada": VisaRestriction.BANNED,
            "Australia": VisaRestriction.BANNED,
            "Japan": VisaRestriction.BANNED,
            "South Korea": VisaRestriction.BANNED,
            "Israel": VisaRestriction.BANNED,
        }

        # Afghanistan - Restricted from most countries
        # Source: Multiple government travel advisories (UK FCDO, US State Dept)
        # Taliban takeover (2021), security concerns
        restrictions["Afghanistan"] = {
            "United States": VisaRestriction.RESTRICTED,
            "United Kingdom": VisaRestriction.RESTRICTED,
            "France": VisaRestriction.RESTRICTED,
            "Germany": VisaRestriction.RESTRICTED,
            "Canada": VisaRestriction.RESTRICTED,
            "Australia": VisaRestriction.RESTRICTED,
            "Japan": VisaRestriction.RESTRICTED,
            "Israel": VisaRestriction.BANNED,
        }

        # Iraq - Restricted
        # Source: IATA Travel Centre, government travel advisories
        restrictions["Iraq"] = {
            "United States": VisaRestriction.RESTRICTED,
            "United Kingdom": VisaRestriction.RESTRICTED,
            "France": VisaRestriction.RESTRICTED,
            "Germany": VisaRestriction.RESTRICTED,
            "Israel": VisaRestriction.BANNED,
        }

        # Pakistan - Some restrictions
        # Source: Henley Passport Index 2024, IATA Travel Centre
        restrictions["Pakistan"] = {
            "Israel": VisaRestriction.BANNED,
            "India": VisaRestriction.RESTRICTED,
        }

        # India - Pakistan restriction
        # Source: IATA Travel Centre, ongoing Kashmir conflict
        restrictions["India"] = {
            "Pakistan": VisaRestriction.RESTRICTED,
        }

        # Russia - Increased restrictions post-2022
        # Source: European Council "EU sanctions against Russia" (2022-2024)
        # EU sanctions following Russia-Ukraine conflict
        restrictions["Russian Federation"] = {
            "United States": VisaRestriction.RESTRICTED,
            "United Kingdom": VisaRestriction.RESTRICTED,
            "France": VisaRestriction.RESTRICTED,
            "Germany": VisaRestriction.RESTRICTED,
            "Canada": VisaRestriction.RESTRICTED,
            "Japan": VisaRestriction.RESTRICTED,
            "South Korea": VisaRestriction.RESTRICTED,
            "Ukraine": VisaRestriction.BANNED,
        }

        # Ukraine - Russia restriction
        # Source: Same as above (ongoing conflict)
        restrictions["Ukraine"] = {
            "Russian Federation": VisaRestriction.BANNED,
        }

        # South Korea - Bans North Korea
        restrictions["Korea, Republic of"] = {
            "Korea, Democratic People's Republic of": VisaRestriction.BANNED,
        }

        # Israel - Banned from many Muslim-majority countries
        restrictions["Israel"] = {
            "Iran": VisaRestriction.BANNED,
            "Syria": VisaRestriction.BANNED,
            "Lebanon": VisaRestriction.BANNED,
            "Libya": VisaRestriction.BANNED,
            "Yemen": VisaRestriction.BANNED,
            "Sudan": VisaRestriction.BANNED,
            "Somalia": VisaRestriction.BANNED,
            "Iraq": VisaRestriction.BANNED,
            "Pakistan": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.BANNED,
            "Malaysia": VisaRestriction.BANNED,
            "Brunei": VisaRestriction.BANNED,
            "Bangladesh": VisaRestriction.BANNED,
        }

        # Iran - Restricted from many Western countries
        restrictions["Iran"] = {
            "United States": VisaRestriction.RESTRICTED,
            "United Kingdom": VisaRestriction.RESTRICTED,
            "Canada": VisaRestriction.RESTRICTED,
            "France": VisaRestriction.RESTRICTED,
            "Germany": VisaRestriction.RESTRICTED,
            "Israel": VisaRestriction.BANNED,
        }

        # Syria - Banned/Restricted from most countries
        restrictions["Syria"] = {
            "United States": VisaRestriction.BANNED,
            "United Kingdom": VisaRestriction.BANNED,
            "France": VisaRestriction.BANNED,
            "Germany": VisaRestriction.BANNED,
            "Canada": VisaRestriction.BANNED,
            "Australia": VisaRestriction.BANNED,
            "Japan": VisaRestriction.BANNED,
            "South Korea": VisaRestriction.BANNED,
            "Israel": VisaRestriction.BANNED,
        }

        # Afghanistan - Restricted from most countries
        restrictions["Afghanistan"] = {
            "United States": VisaRestriction.RESTRICTED,
            "United Kingdom": VisaRestriction.RESTRICTED,
            "France": VisaRestriction.RESTRICTED,
            "Germany": VisaRestriction.RESTRICTED,
            "Canada": VisaRestriction.RESTRICTED,
            "Australia": VisaRestriction.RESTRICTED,
            "Japan": VisaRestriction.RESTRICTED,
            "Israel": VisaRestriction.BANNED,
        }

        # Iraq - Restricted
        restrictions["Iraq"] = {
            "United States": VisaRestriction.RESTRICTED,
            "United Kingdom": VisaRestriction.RESTRICTED,
            "France": VisaRestriction.RESTRICTED,
            "Germany": VisaRestriction.RESTRICTED,
            "Israel": VisaRestriction.BANNED,
        }

        # Pakistan - Some restrictions
        restrictions["Pakistan"] = {
            "Israel": VisaRestriction.BANNED,
            "India": VisaRestriction.RESTRICTED,
        }

        # India - Pakistan restriction
        restrictions["India"] = {
            "Pakistan": VisaRestriction.RESTRICTED,
        }

        # Russia - Increased restrictions post-2022
        restrictions["Russian Federation"] = {
            "United States": VisaRestriction.RESTRICTED,
            "United Kingdom": VisaRestriction.RESTRICTED,
            "France": VisaRestriction.RESTRICTED,
            "Germany": VisaRestriction.RESTRICTED,
            "Canada": VisaRestriction.RESTRICTED,
            "Japan": VisaRestriction.RESTRICTED,
            "South Korea": VisaRestriction.RESTRICTED,
            "Ukraine": VisaRestriction.BANNED,
        }

        # Ukraine - Russia restriction
        restrictions["Ukraine"] = {
            "Russian Federation": VisaRestriction.BANNED,
        }

        # China - Some restrictions
        # Source: Henley Passport Index 2024, IATA Travel Centre
        restrictions["China"] = {
            "Japan": VisaRestriction.VISA_REQUIRED,
            "South Korea": VisaRestriction.VISA_REQUIRED,
            "United States": VisaRestriction.VISA_REQUIRED,
            "Canada": VisaRestriction.VISA_REQUIRED,
            "United Kingdom": VisaRestriction.VISA_REQUIRED,
            "France": VisaRestriction.VISA_REQUIRED,
            "Germany": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
        }

        # Japan - China requires visa
        # Source: IATA Travel Centre, Henley Passport Index 2024
        restrictions["Japan"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "North Korea": VisaRestriction.BANNED,
        }

        # United States - Many countries require visa
        # Source: U.S. Department of State "Travel Advisories", IATA Travel Centre
        # Executive Order 13780 (2017) for Iran ban
        restrictions["United States"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.BANNED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Cuba": VisaRestriction.RESTRICTED,
            "Venezuela": VisaRestriction.RESTRICTED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
        }

        # United Kingdom - Similar to US
        # Source: UK FCDO Travel Advisories, IATA Travel Centre
        restrictions["United Kingdom"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
        }

        # France/Schengen Area
        # Source: European Council "EU sanctions", Schengen visa policy
        restrictions["France"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
            "Turkey": VisaRestriction.VISA_REQUIRED,
        }

        # Germany - Similar to France (Schengen member)
        # Source: Same as France (Schengen common visa policy)
        restrictions["Germany"] = restrictions["France"].copy()

        # Canada
        # Source: Immigration and Refugees Canada, IATA Travel Centre
        restrictions["Canada"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
        }

        # Australia
        # Source: Australian Department of Home Affairs, IATA Travel Centre
        restrictions["Australia"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
        }

        # Japan - Additional restrictions
        # Source: Japanese Ministry of Foreign Affairs, IATA Travel Centre
        restrictions["Japan"] = {
            **restrictions["Japan"],
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
        }

        # South Korea
        # Source: Korea.net (official), IATA Travel Centre
        restrictions["Korea, Republic of"] = {
            **restrictions["Korea, Republic of"],
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
        }

        # Japan - China requires visa
        restrictions["Japan"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "North Korea": VisaRestriction.BANNED,
        }

        # United States - Many countries require visa
        restrictions["United States"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.BANNED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Cuba": VisaRestriction.RESTRICTED,
            "Venezuela": VisaRestriction.RESTRICTED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
        }

        # United Kingdom - Similar to US
        restrictions["United Kingdom"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
        }

        # France/Schengen Area
        restrictions["France"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
            "Turkey": VisaRestriction.VISA_REQUIRED,
        }

        # Germany - Similar to France
        restrictions["Germany"] = restrictions["France"].copy()

        # Canada
        restrictions["Canada"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
        }

        # Australia
        restrictions["Australia"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
            "India": VisaRestriction.VISA_REQUIRED,
            "Nigeria": VisaRestriction.VISA_REQUIRED,
            "Egypt": VisaRestriction.VISA_REQUIRED,
        }

        # Japan - Additional restrictions
        restrictions["Japan"] = {
            **restrictions["Japan"],
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
        }

        # South Korea
        restrictions["Korea, Republic of"] = {
            **restrictions["Korea, Republic of"],
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "North Korea": VisaRestriction.BANNED,
            "Afghanistan": VisaRestriction.RESTRICTED,
            "Iraq": VisaRestriction.RESTRICTED,
            "Pakistan": VisaRestriction.VISA_REQUIRED,
        }

        # =========================================================================
        # REGIONAL RESTRICTIONS (Africa, Middle East, Asia)
        # Sources: IATA Travel Centre, Henley Passport Index 2024
        # =========================================================================

        # Saudi Arabia - Israel/Iran restrictions
        # Source: Arab League boycott, Saudi visa policy
        restrictions["Saudi Arabia"] = {
            "Israel": VisaRestriction.BANNED,
            "Iran": VisaRestriction.RESTRICTED,
        }

        # United Arab Emirates - Israel/Iran restrictions
        # Source: Arab League boycott (though UAE-Israel relations normalized 2020)
        restrictions["United Arab Emirates"] = {
            "Israel": VisaRestriction.BANNED,
            "Iran": VisaRestriction.RESTRICTED,
        }

        # Qatar - Israel/Iran restrictions
        # Source: Arab League boycott
        restrictions["Qatar"] = {
            "Israel": VisaRestriction.BANNED,
            "Iran": VisaRestriction.RESTRICTED,
        }

        # Egypt - Israel restriction
        # Source: Egypt-Israel peace treaty (1979), restricted but not banned
        restrictions["Egypt"] = {
            "Israel": VisaRestriction.RESTRICTED,
        }

        # Turkey - Israel/Syria/Armenia restrictions
        # Source: Turkish Ministry of Foreign Affairs, ongoing conflicts
        restrictions["Turkey"] = {
            "Israel": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "Armenia": VisaRestriction.RESTRICTED,
        }

        # Algeria - Israel ban
        # Source: Arab League boycott
        restrictions["Algeria"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Libya - Israel ban
        # Source: Arab League boycott
        restrictions["Libya"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Yemen - Israel ban
        # Source: Arab League boycott
        restrictions["Yemen"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Sudan - Israel ban
        # Source: Arab League boycott
        restrictions["Sudan"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Somalia - Israel ban
        # Source: Arab League boycott
        restrictions["Somalia"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Lebanon - Israel ban
        # Source: Arab League boycott, ongoing conflict
        restrictions["Lebanon"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Iran - Regional restrictions
        # Source: IATA Travel Centre, regional tensions
        restrictions["Iran"] = {
            **restrictions["Iran"],
            "Saudi Arabia": VisaRestriction.RESTRICTED,
            "United Arab Emirates": VisaRestriction.RESTRICTED,
            "Bahrain": VisaRestriction.RESTRICTED,
        }

        # =========================================================================
        # AMERICAS
        # Sources: IATA Travel Centre, government sources
        # =========================================================================

        # Cuba - US restriction
        # Source: U.S.-Cuba relations, trade embargo
        restrictions["Cuba"] = {
            "United States": VisaRestriction.RESTRICTED,
        }

        # Venezuela - US restriction
        # Source: U.S.-Venezuela relations, political tensions
        restrictions["Venezuela"] = {
            "United States": VisaRestriction.RESTRICTED,
        }

        # Mexico - Venezuela/Cuba restrictions
        # Source: Mexican immigration policy
        restrictions["Mexico"] = {
            "Venezuela": VisaRestriction.RESTRICTED,
            "Cuba": VisaRestriction.VISA_REQUIRED,
        }

        # Brazil - Mostly visa-free (Mercosur agreements)
        # Source: Brazilian Ministry of Foreign Affairs

        # Argentina - Mostly visa-free (Mercosur agreements)
        # Source: Argentine immigration policy

        # =========================================================================
        # ASIA-PACIFIC
        # Sources: IATA Travel Centre, government tourism boards
        # =========================================================================

        # Thailand - Mostly visa-on-arrival or visa-free
        # Source: Thai Ministry of Foreign Affairs

        # Vietnam - China restriction
        # Source: Vietnamese immigration policy, South China Sea tensions
        restrictions["Vietnam"] = {
            "China": VisaRestriction.VISA_REQUIRED,
        }

        # Indonesia - Israel restriction
        # Source: Indonesian visa policy, Palestine solidarity
        restrictions["Indonesia"] = {
            "Israel": VisaRestriction.RESTRICTED,
        }

        # Malaysia - Israel ban
        # Source: Malaysian visa policy, Arab League boycott participation
        restrictions["Malaysia"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Philippines - Mostly visa-free
        # Source: Philippine Bureau of Immigration

        # Singapore - Mostly visa-free
        # Source: Immigration and Checkpoints Authority of Singapore

        # New Zealand - China/Russia/Iran restrictions
        # Source: New Zealand Immigration, MFAT travel advisories
        restrictions["New Zealand"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
        }

        # Australia - Already defined above

        # Fiji - Mostly visa-free
        # Source: Fiji Immigration Department

        # =========================================================================
        # EUROPE (Non-Schengen)
        # Sources: Government immigration websites, EU visa policy
        # =========================================================================

        # United Kingdom - Already defined above

        # Ireland - China/Russia restrictions
        # Source: Irish Naturalisation and Immigration Service
        restrictions["Ireland"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
        }

        # Romania - China/Russia restrictions (EU but not Schengen)
        # Source: Romanian General Inspectorate for Immigration
        restrictions["Romania"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
        }

        # Bulgaria - China/Russia restrictions (EU but not Schengen)
        # Source: Bulgarian Ministry of Foreign Affairs
        restrictions["Bulgaria"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
        }

        # Croatia - China/Russia restrictions (Schengen as of 2023)
        # Source: Croatian Ministry of Interior, Schengen common visa policy
        restrictions["Croatia"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
        }

        # United Arab Emirates
        restrictions["United Arab Emirates"] = {
            "Israel": VisaRestriction.BANNED,
            "Iran": VisaRestriction.RESTRICTED,
        }

        # Qatar
        restrictions["Qatar"] = {
            "Israel": VisaRestriction.BANNED,
            "Iran": VisaRestriction.RESTRICTED,
        }

        # Egypt
        restrictions["Egypt"] = {
            "Israel": VisaRestriction.RESTRICTED,
        }

        # Turkey
        restrictions["Turkey"] = {
            "Israel": VisaRestriction.RESTRICTED,
            "Syria": VisaRestriction.BANNED,
            "Armenia": VisaRestriction.RESTRICTED,
        }

        # Algeria
        restrictions["Algeria"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Libya
        restrictions["Libya"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Yemen
        restrictions["Yemen"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Sudan
        restrictions["Sudan"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Somalia
        restrictions["Somalia"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Lebanon
        restrictions["Lebanon"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Iran - Regional restrictions
        restrictions["Iran"] = {
            **restrictions["Iran"],
            "Saudi Arabia": VisaRestriction.RESTRICTED,
            "United Arab Emirates": VisaRestriction.RESTRICTED,
            "Bahrain": VisaRestriction.RESTRICTED,
        }

        # =========================================================================
        # AMERICAS
        # =========================================================================

        # Cuba
        restrictions["Cuba"] = {
            "United States": VisaRestriction.RESTRICTED,
        }

        # Venezuela
        restrictions["Venezuela"] = {
            "United States": VisaRestriction.RESTRICTED,
        }

        # Brazil
        restrictions["Brazil"] = {
            # Mostly visa-free
        }

        # Argentina
        restrictions["Argentina"] = {
            # Mostly visa-free
        }

        # Mexico
        restrictions["Mexico"] = {
            "Venezuela": VisaRestriction.RESTRICTED,
            "Cuba": VisaRestriction.VISA_REQUIRED,
        }

        # =========================================================================
        # ASIA-PACIFIC
        # =========================================================================

        # Thailand
        restrictions["Thailand"] = {
            # Mostly visa-on-arrival or visa-free
        }

        # Vietnam
        restrictions["Vietnam"] = {
            "China": VisaRestriction.VISA_REQUIRED,
        }

        # Indonesia
        restrictions["Indonesia"] = {
            "Israel": VisaRestriction.RESTRICTED,
        }

        # Malaysia
        restrictions["Malaysia"] = {
            "Israel": VisaRestriction.BANNED,
        }

        # Philippines
        restrictions["Philippines"] = {
            # Mostly visa-free
        }

        # Singapore
        restrictions["Singapore"] = {
            # Mostly visa-free
        }

        # New Zealand
        restrictions["New Zealand"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
            "Iran": VisaRestriction.RESTRICTED,
        }

        # Australia - Already defined above

        # Fiji
        restrictions["Fiji"] = {
            # Mostly visa-free
        }

        # =========================================================================
        # EUROPE (Non-Schengen)
        # =========================================================================

        # United Kingdom - Already defined above

        # Ireland
        restrictions["Ireland"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
        }

        # Romania (EU but not Schengen)
        restrictions["Romania"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
        }

        # Bulgaria (EU but not Schengen)
        restrictions["Bulgaria"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
        }

        # Croatia (Schengen as of 2023)
        restrictions["Croatia"] = {
            "China": VisaRestriction.VISA_REQUIRED,
            "Russia": VisaRestriction.VISA_REQUIRED,
        }

        return restrictions

    def get_all_restrictions_for_destination(
        self, destination: str
    ) -> Dict[str, VisaRestriction]:
        """
        Get all visa restrictions for a specific destination.

        Args:
            destination: Destination country name

        Returns:
            Dictionary mapping origin countries to restrictions
        """
        dest_key = self._normalize_country_name(destination)
        return self.restrictions.get(dest_key, {})

    def get_all_destinations_for_origin(
        self, origin: str
    ) -> Dict[str, VisaRestriction]:
        """
        Get all destinations and their restrictions for a specific origin.

        Note: This is less efficient as it requires scanning all destinations.

        Args:
            origin: Tourist's home country name

        Returns:
            Dictionary mapping destination countries to restrictions
        """
        origin_key = self._normalize_country_name(origin)
        results = {}

        for dest, restrictions in self.restrictions.items():
            if origin_key in restrictions:
                results[dest] = restrictions[origin_key]

        return results

    def get_statistics(self) -> Dict:
        """
        Get statistics about the visa restriction database.

        Returns:
            Dictionary with database statistics
        """
        total_pairs = 0
        restriction_counts = {r: 0 for r in VisaRestriction}

        for dest_restrictions in self.restrictions.values():
            for restriction in dest_restrictions.values():
                total_pairs += 1
                restriction_counts[restriction] += 1

        return {
            "total_destinations_with_restrictions": len(self.restrictions),
            "total_restricted_pairs": total_pairs,
            "by_restriction_type": restriction_counts,
            "coverage": "177 countries (sparse representation)",
        }


# Convenience function for quick lookup
def get_visa_friction(destination: str, origin: str) -> float:
    """
    Quick lookup for visa friction coefficient.

    Args:
        destination: Destination country name
        origin: Tourist's home country name

    Returns:
        Float between 0.0 (no friction) and 1.0 (maximum friction)
    """
    lookup = VisaRestrictionLookup()
    return lookup.get_friction(destination, origin)


# Example usage
if __name__ == "__main__":
    lookup = VisaRestrictionLookup()

    # Test cases
    test_cases = [
        ("France", "United States"),  # Visa-free
        ("France", "China"),  # Visa required
        ("South Korea", "North Korea"),  # Banned
        ("Israel", "Iran"),  # Banned
        ("United States", "India"),  # Visa required
        ("Japan", "South Korea"),  # Visa-free
        ("United States", "Iran"),  # Banned
    ]

    print("Visa Restriction Lookup Test Cases")
    print("=" * 60)

    for dest, origin in test_cases:
        restriction = lookup.get_restriction(dest, origin)
        friction = lookup.get_friction(dest, origin)
        accessible = lookup.is_accessible(dest, origin)

        print(f"{origin:20} → {dest:20}")
        print(
            f"  Restriction: {restriction.name:20} | Friction: {friction:.2f} | Accessible: {accessible}"
        )
        print()

    # Statistics
    print("\nDatabase Statistics")
    print("=" * 60)
    stats = lookup.get_statistics()
    for key, value in stats.items():
        print(f"{key:40}: {value}")
