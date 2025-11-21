# DressedUp

**Your intelligent wardrobe assistant**

## Overview

DressedUp is an intelligent wardrobe assistant mobile app that helps users organize their closet, get daily outfit suggestions based on weather and occasion, track clean/dirty clothes, discover shopping recommendations, share fits with friends via streaks, and pack smartly for trips. Built with React Native for seamless iOS and Android experiences.

## Core Features

### Digital Closet
- Photo-based item cataloging with AI tagging
- Organization by category, brand, occasion, and color
- Clean/dirty status tracking
- 47 items capacity with extensibility

### Smart Outfit Suggestions
- Weather-aware recommendations
- Occasion-based filtering (Work, Casual, Gym, Date, Formal, Night Out)
- Multi-context planning for multiple daily events
- Item swapping and alternative outfit options
- 138+ outfit combinations from user's closet

### Social Feed
- Share daily outfit videos (10-second max)
- Tag items in posts with visual overlays
- Clone outfits from friends
- React and comment on posts
- Track posting streaks

### Shopping Integration
- Identify missing items from cloned outfits
- Direct purchase links for suggested items
- Match items from user's closet to complete looks

### Trip Planning (Premium)
- Destination-based packing lists
- Weather-aware clothing recommendations
- Checklist functionality with progress tracking

### Additional Features
- Laundry reminders and clean item tracking
- Daily outfit suggestions for established routines
- Closet statistics and insights
- Calendar integration for scheduled events
- Friend circles for private sharing (Premium)
- Couples outfit coordination (Premium)

## User Flow

1. **Onboarding**: Sign up → Learn features → Build digital closet (min 10 items)
2. **Daily Use**: Check suggestions → Select or swap items → Confirm outfit → Mark as worn
3. **Social**: Browse feed → Post outfit video → Tag items → Engage with friends
4. **Management**: Track clean/dirty items → Review stats → Plan trips → Shop missing pieces

## Subscription Model

### Free Trial
- 45-day premium trial
- Limited daily suggestions
- Public feed access only

### Premium ($5.99/mo)
- Unlimited daily outfit suggestions
- Private friend circles
- Couples fit planning
- Trip packing assistant
- Cancel anytime

## Navigation Structure

**Bottom Nav (5 tabs)**
- 🏠 Home: Daily suggestions and quick stats
- 👔 Closet: Item management and browsing
- 📱 Feed: Social posts and cloning
- 🛍️ Shop: Purchase recommendations
- 👤 Profile: Settings, stats, trips, circles

## Key Screens

### Home Screen
**New User**: Manual "Get Dressed" flow with occasion selection
**Established User**: Automatic multi-context suggestions based on learned routine

### Closet Views
- Grid view with filter tabs (All, By Type, By Brand, By Occasion)
- Clean/Dirty toggle
- Available fits counter
- Item detail pages with edit/delete options

### Daily Outfit Flow
1. Occasion selection
2. AI-generated suggestion
3. Item swap options
4. Alternative complete outfits
5. Confirmation with worn status update

### Feed
- Vertical scroll of video posts
- Post detail view with tagged items
- Clone feature with item matching
- Recording interface with 10s limit
- Item tagging overlay

## Technical Notes

- Mobile-first design (390x844px)
- Emoji-based item representation in wireframe
- Real-time weather integration
- Calendar sync for routine learning
- Photo capture and AI categorization
- Clean/dirty state management

## Settings

- Profile editing
- Password management
- Calendar connections
- Notification preferences (Daily fit, Laundry, Shopping)
- Privacy policy and terms
- Help & support

## Statistics Tracked

- Total items in closet
- Clean vs dirty item count
- Available outfit combinations
- Posting streak (days)
- Total fits created
- Items by category breakdown
