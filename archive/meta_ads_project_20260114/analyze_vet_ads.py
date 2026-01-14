#!/usr/bin/env python3
"""
Analyze collected Meta Ad Library data
Categorize ads by type and performance
"""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter


class VetAdAnalyzer:
    """Analyze vet clinic ads for patterns and performance"""
    
    def __init__(self, tsv_path: str):
        self.tsv_path = tsv_path
        self.ads = []
        self.load_data()
    
    def load_data(self):
        """Load ads from TSV file"""
        with open(self.tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            self.ads = list(reader)
        
        print(f"Loaded {len(self.ads)} ads from {self.tsv_path}")
    
    def categorize_ad_type(self, ad: Dict) -> str:
        """
        Categorize ad by content type
        
        Returns:
            Category name
        """
        text = f"{ad.get('ad_text', '')} {ad.get('ad_caption', '')} {ad.get('ad_title', '')}".lower()
        
        # Promotional keywords
        promo_keywords = [
            'ფასდაკლება', 'скидка', 'discount', 'акция', 'შეთავაზება',
            '%', 'უფასო', 'бесплатно', 'free', 'გამარჯვებული'
        ]
        
        # Educational keywords
        edu_keywords = [
            'რჩევა', 'совет', 'tip', 'როგორ', 'как', 'how',
            'ინფორმაცია', 'информация', 'info', 'ჯანმრთელობა', 'здоровье', 'health'
        ]
        
        # Emotional keywords
        emotional_keywords = [
            'გადარჩენა', 'спасение', 'rescue', 'ისტორია', 'история', 'story',
            'მადლობა', 'спасибо', 'thank', 'სიყვარული', 'любовь', 'love'
        ]
        
        # Service keywords
        service_keywords = [
            'ვაქცინაცია', 'вакцинация', 'vaccination', 'ოპერაცია', 'операция', 'surgery',
            'სტერილიზაცია', 'стерилизация', 'sterilization', 'კონსულტაცია', 'консультация', 'consultation'
        ]
        
        # Emergency keywords
        emergency_keywords = [
            'გადაუდებელი', 'срочно', 'emergency', '24/7', 'ღამის', 'ночной', 'night'
        ]
        
        # Check categories in priority order
        if any(kw in text for kw in emergency_keywords):
            return "Emergency/24-7"
        elif any(kw in text for kw in promo_keywords):
            return "Promotional"
        elif any(kw in text for kw in service_keywords):
            return "Service-Focused"
        elif any(kw in text for kw in emotional_keywords):
            return "Emotional"
        elif any(kw in text for kw in edu_keywords):
            return "Educational"
        else:
            return "Other"
    
    def calculate_performance_score(self, ad: Dict) -> Tuple[int, str]:
        """
        Calculate performance score based on available metrics
        
        Returns:
            (score, reason)
        """
        score = 0
        reasons = []
        
        # Days running (long-running = proven winner)
        try:
            days = int(ad.get('days_running', 0))
            if days > 90:
                score += 30
                reasons.append(f"Long-running ({days} days)")
            elif days > 30:
                score += 20
                reasons.append(f"Medium-running ({days} days)")
            elif days > 7:
                score += 10
                reasons.append(f"Short-running ({days} days)")
        except:
            pass
        
        # Still active
        if ad.get('is_active') == 'Yes':
            score += 20
            reasons.append("Currently active")
        
        # Has impressions data
        if ad.get('impressions_min'):
            try:
                imp_min = int(ad.get('impressions_min', 0))
                if imp_min > 10000:
                    score += 30
                    reasons.append(f"High impressions ({imp_min:,}+)")
                elif imp_min > 5000:
                    score += 20
                    reasons.append(f"Medium impressions ({imp_min:,}+)")
                elif imp_min > 1000:
                    score += 10
                    reasons.append(f"Low impressions ({imp_min:,}+)")
            except:
                pass
        
        # Has spend data (serious advertiser)
        if ad.get('spend_min'):
            score += 10
            reasons.append("Has spend data")
        
        reason_text = "; ".join(reasons) if reasons else "No metrics available"
        return score, reason_text
    
    def analyze(self) -> Dict:
        """
        Perform full analysis
        
        Returns:
            Analysis results dictionary
        """
        print("\n" + "=" * 60)
        print("ANALYZING VET CLINIC ADS")
        print("=" * 60)
        
        # Categorize all ads
        for ad in self.ads:
            ad['category'] = self.categorize_ad_type(ad)
            ad['performance_score'], ad['performance_reason'] = self.calculate_performance_score(ad)
        
        # Statistics
        total_ads = len(self.ads)
        active_ads = len([a for a in self.ads if a.get('is_active') == 'Yes'])
        
        # Category distribution
        categories = Counter(ad['category'] for ad in self.ads)
        
        # Advertiser distribution
        advertisers = Counter(ad['advertiser'] for ad in self.ads)
        
        # Top performers
        top_performers = sorted(self.ads, key=lambda x: int(x.get('performance_score', 0)), reverse=True)[:10]
        
        # Language detection
        georgian_ads = len([a for a in self.ads if self.contains_georgian(a)])
        russian_ads = len([a for a in self.ads if self.contains_russian(a)])
        
        results = {
            'total_ads': total_ads,
            'active_ads': active_ads,
            'categories': categories,
            'advertisers': advertisers,
            'top_performers': top_performers,
            'georgian_ads': georgian_ads,
            'russian_ads': russian_ads,
        }
        
        return results
    
    def contains_georgian(self, ad: Dict) -> bool:
        """Check if ad contains Georgian text"""
        text = f"{ad.get('ad_text', '')} {ad.get('ad_caption', '')}"
        return bool(re.search(r'[\u10A0-\u10FF]', text))
    
    def contains_russian(self, ad: Dict) -> bool:
        """Check if ad contains Russian text"""
        text = f"{ad.get('ad_text', '')} {ad.get('ad_caption', '')}"
        return bool(re.search(r'[А-Яа-яЁё]', text))
    
    def print_report(self, results: Dict):
        """Print analysis report"""
        print(f"\n📊 OVERVIEW")
        print(f"Total ads collected: {results['total_ads']}")
        print(f"Currently active: {results['active_ads']}")
        print(f"Georgian language: {results['georgian_ads']}")
        print(f"Russian language: {results['russian_ads']}")
        
        print(f"\n📁 CATEGORIES")
        for category, count in results['categories'].most_common():
            pct = (count / results['total_ads']) * 100
            print(f"  {category}: {count} ({pct:.1f}%)")
        
        print(f"\n🏢 TOP ADVERTISERS")
        for advertiser, count in results['advertisers'].most_common(10):
            print(f"  {advertiser}: {count} ads")
        
        print(f"\n🏆 TOP 10 PERFORMING ADS")
        for i, ad in enumerate(results['top_performers'], 1):
            score = ad.get('performance_score', 0)
            advertiser = ad.get('advertiser', 'Unknown')
            category = ad.get('category', 'Unknown')
            reason = ad.get('performance_reason', 'N/A')
            
            print(f"\n  #{i} - Score: {score}")
            print(f"      Advertiser: {advertiser}")
            print(f"      Category: {category}")
            print(f"      Reason: {reason}")
            print(f"      URL: {ad.get('ad_snapshot_url', 'N/A')}")
    
    def save_analyzed_data(self, output_path: str):
        """Save analyzed data with categories and scores"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not self.ads:
                return
            
            fieldnames = list(self.ads[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            writer.writerows(self.ads)
        
        print(f"\n💾 Saved analyzed data to: {output_path}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Meta Ad Library data for vet clinics")
    parser.add_argument("--input", type=str, default=".tmp/vet_ads_georgia.tsv", help="Input TSV file")
    parser.add_argument("--output", type=str, default=".tmp/vet_ads_analyzed.tsv", help="Output TSV file")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        print(f"\nPlease run meta_ad_library.py first to collect data:")
        print(f"  python3 meta_ad_library.py --all-keywords")
        return
    
    # Analyze
    analyzer = VetAdAnalyzer(args.input)
    results = analyzer.analyze()
    analyzer.print_report(results)
    analyzer.save_analyzed_data(args.output)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
