import argparse
import pandas as pd
from src.extractor import geocode_address, get_pois, get_pois_with_detailed_categories, create_grid_analysis, create_grid_analysis_vertical

def main():
    parser = argparse.ArgumentParser(description="Extract POIs from OpenStreetMap.")
    parser.add_argument("--address", type=str, help="Address to search for.")
    parser.add_argument("--lat", type=float, help="Latitude of the center point.")
    parser.add_argument("--lon", type=float, help="Longitude of the center point.")
    parser.add_argument("--output", type=str, default="pois.csv", help="Output CSV file name.")
    parser.add_argument("--analysis", type=str, choices=["individual", "grid", "grid-vertical"], default="individual", 
                       help="Analysis type: 'individual' for individual POIs, 'grid' for horizontal grid analysis, 'grid-vertical' for vertical grid analysis")
    parser.add_argument("--radius", type=float, default=5.0, 
                       help="Search radius in km for grid analysis (default: 5.0)")
    parser.add_argument("--grid-size", type=float, default=0.5, 
                       help="Grid cell size in km (default: 0.5)")
    
    args = parser.parse_args()
    
    lat, lon = None, None
    
    if args.address:
        lat, lon = geocode_address(args.address)
        if not lat:
            print(f"Could not geocode address: {args.address}")
            return
            
    elif args.lat and args.lon:
        lat, lon = args.lat, args.lon
    
    else:
        print("Please provide either an address or latitude/longitude.")
        parser.print_help()
        return

    print(f"Searching for POIs around ({lat}, {lon})...")
    
    if args.analysis == "individual":
        pois_df = get_pois_with_detailed_categories(lat, lon)
        
        if pois_df.empty:
            print("No POIs found in the specified area.")
        else:
            pois_df.to_csv(args.output, index=False)
            print(f"Successfully extracted {len(pois_df)} POIs to {args.output}")
            
            # Print summary
            print("\nCategory summary:")
            category_counts = pois_df['category'].value_counts()
            for category, count in category_counts.items():
                print(f"  {category}: {count}")
    
    elif args.analysis == "grid":  # horizontal grid analysis
        print(f"Performing grid analysis with {args.radius}km radius and {args.grid_size}km cells...")
        grid_df = create_grid_analysis(lat, lon, grid_size_km=args.grid_size, search_radius_km=args.radius)
        
        if grid_df.empty:
            print("No POIs found in the specified area.")
        else:
            grid_df.to_csv(args.output, index=False)
            print(f"Successfully created grid analysis with {len(grid_df)} grid cells to {args.output}")
            
            # Print summary
            print("\nTotal counts across all grid cells:")
            summary_cols = [col for col in grid_df.columns if col.endswith('_count')]
            for col in summary_cols:
                total = grid_df[col].sum()
                if total > 0:
                    category = col.replace('_count', '')
                    print(f"  {category}: {total}")
    
    else:  # vertical grid analysis
        print(f"Performing vertical grid analysis with {args.radius}km radius and {args.grid_size}km cells...")
        grid_df = create_grid_analysis_vertical(lat, lon, grid_size_km=args.grid_size, search_radius_km=args.radius)
        
        if grid_df.empty:
            print("No POIs found in the specified area.")
        else:
            grid_df.to_csv(args.output, index=False)
            print(f"Successfully created vertical grid analysis with {len(grid_df)} POIs to {args.output}")
            
            # Print summary
            print("\nTotal counts across all grid cells:")
            summary_df = grid_df.groupby('category')['count'].sum()
            for category, total in summary_df.items():
                if total > 0:
                    print(f"  {category}: {total}")

if __name__ == "__main__":
    main()
