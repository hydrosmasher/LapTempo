SwimForge Assets
-----------------
Files:
- assets/banner.svg  (includes "Powered by HydroSmasher")
- assets/logo.svg
- assets/banner.png  (generate with cairosvg if this is a placeholder)
- assets/logo.png    (generate with cairosvg if this is a placeholder)

Integrate in app.py:
- At the top of landing_page() and race_split_page(), add:
    st.image('assets/banner.png', use_column_width=True)

- In the sidebar (e.g., in app_nav() before 'Account'):
    st.sidebar.image('assets/logo.png', width=72)
