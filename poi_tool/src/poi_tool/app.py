import streamlit as st
import pandas as pd
from src.extractor import geocode_address, get_pois, get_pois_with_detailed_categories, create_grid_analysis, create_grid_analysis_vertical

st.title("POI Extraction Tool")

st.markdown("""
This tool allows you to extract Points of Interest (POIs) from OpenStreetMap.
Enter an address or latitude/longitude to get started.

**New Features:**
- Grid-by-grid analysis (0.5 km² cells)
- New categories: Public Schools, Public Transit Lines, Parks and Recreational Areas, Community Services, Cafés, Bars, Libraries, Housing (Single-Family, Residential Buildings, Detached, Semi-Detached, Terraced, Residential Areas)
- CSV export with category counts per grid cell (vertical format)
""")

# Analysis type selection
analysis_type = st.radio(
    "Select analysis type:",
    ["Individual POIs", "Grid Analysis (0.5 km² cells)"],
    help="Grid analysis provides counts of each category per 0.5 km² grid cell"
)

address = st.text_input("Enter an address")
lat = st.number_input("Or enter Latitude", format="%.6f")
lon = st.number_input("And Longitude", format="%.6f")

# Grid analysis parameters
if analysis_type == "Grid Analysis (0.5 km² cells)":
    search_radius = st.slider("Search radius (km)", 0.5, 10.0, 5.0, help="Radius around the center point to analyze")
    if search_radius == 0.5:
        st.info("Will create a 1x1 km grid with 0.5 km² cells")
    else:
        st.info(f"Will create a {search_radius*2}x{search_radius*2} km grid with 0.5 km² cells")

if st.button("Extract POIs"):
    if address:
        latitude, longitude = geocode_address(address)
        if not latitude:
            st.error("Could not geocode address. Please try again.")
        else:
            st.success(f"Geocoded address to: ({latitude}, {longitude})")
            
            if analysis_type == "Individual POIs":
                df = get_pois_with_detailed_categories(latitude, longitude)
                if not df.empty:
                    st.success(f"Found {len(df)} POIs.")
                    st.dataframe(df)
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download data as CSV",
                        data=csv,
                        file_name='pois.csv',
                        mime='text/csv',
                    )
                else:
                    st.warning("No POIs found in the specified area.")
            else:
                # Grid analysis
                with st.spinner("Performing grid analysis... This may take a few minutes."):
                    df = create_grid_analysis_vertical(latitude, longitude, search_radius_km=search_radius)
                
                if not df.empty:
                    st.success(f"Grid analysis complete! Found {len(df)} POIs across all grid cells.")
                    
                    # Display summary statistics
                    st.subheader("Summary Statistics")
                    summary_df = df.groupby('category')['count'].sum().reset_index()
                    summary_df = summary_df[summary_df['count'] > 0].sort_values('count', ascending=False)
                    summary_df.columns = ['Category', 'Total Count']
                    st.dataframe(summary_df)
                    
                    # Display grid data
                    st.subheader("Grid Cell Data")
                    st.dataframe(df)
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download grid analysis as CSV",
                        data=csv,
                        file_name=f'poi_grid_analysis_{search_radius}km.csv',
                        mime='text/csv',
                    )
                else:
                    st.warning("No POIs found in the specified area.")

    elif lat and lon:
        if analysis_type == "Individual POIs":
            df = get_pois_with_detailed_categories(lat, lon)
            if not df.empty:
                st.success(f"Found {len(df)} POIs.")
                st.dataframe(df)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name='pois.csv',
                    mime='text/csv',
                )
            else:
                st.warning("No POIs found in the specified area.")
        else:
            # Grid analysis
            with st.spinner("Performing grid analysis... This may take a few minutes."):
                df = create_grid_analysis_vertical(lat, lon, search_radius_km=search_radius)
            
            if not df.empty:
                st.success(f"Grid analysis complete! Found {len(df)} POIs across all grid cells.")
                
                # Display summary statistics
                st.subheader("Summary Statistics")
                summary_df = df.groupby('category')['count'].sum().reset_index()
                summary_df = summary_df[summary_df['count'] > 0].sort_values('count', ascending=False)
                summary_df.columns = ['Category', 'Total Count']
                st.dataframe(summary_df)
                
                # Display grid data
                st.subheader("Grid Cell Data")
                st.dataframe(df)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download grid analysis as CSV",
                    data=csv,
                    file_name=f'poi_grid_analysis_{search_radius}km.csv',
                    mime='text/csv',
                )
            else:
                st.warning("No POIs found in the specified area.")

    else:
        st.warning("Please enter an address or coordinates.")
