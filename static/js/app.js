// A global function for toggling collapsible sections, as it's called directly from the HTML
function toggleSection(section) {
    const content = document.getElementById(`${section}-content`);
    const header = content.previousElementSibling;
    const title = header.querySelector('.section-title');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        title.textContent = title.textContent.replace('▶', '▼');
    } else {
        content.style.display = 'none';
        title.textContent = title.textContent.replace('▼', '▶');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const loadingIndicator = document.getElementById('loading-indicator');

    // --- Main ---
    
    function initDashboard() {
        console.log("Initializing dashboard...");
        showLoading();
        fetchData();
        updateTimestamp();
        setInterval(updateTimestamp, 1000 * 60); // Update timestamp every minute
    }

    async function fetchData() {
        try {
            const response = await fetch('/api/market-data');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            updateUI(data);
        } catch (error) {
            console.error("Failed to fetch or process market data:", error);
            document.querySelector('.dashboard-container').innerHTML = `<div style="text-align: center; padding: 50px; color: #F87171;"><h2>Error</h2><p>Could not load market data. Please try again later.</p><p><i>${error.message}</i></p></div>`;
        } finally {
            hideLoading();
            // Initialize read more functionality after UI is loaded
            setTimeout(initializeReadMore, 100);
        }
    }

    function updateUI(data) {
        if (!data || !data.fear_and_greed || !data.aaii_sentiment) {
            console.error("Incomplete data received from API.");
            return;
        }
        
        // Pass historical time series data to renderFearGreed so components can access it
        const fngDataWithHistorical = {
            ...data.fear_and_greed,
            historicalTimeSeries: data.fear_and_greed.historical_time_series || {}
        };
        
        renderFearGreed(fngDataWithHistorical);
        renderAaiiSentiment(data.aaii_sentiment);
        
        // Render SSI if available
        if (data.bank_of_america_ssi) {
            renderSSI(data.bank_of_america_ssi);
        }
        
        const spread = data.aaii_sentiment.bullish - data.aaii_sentiment.bearish;

        if (data.overall_analysis && data.overall_analysis.recommendation) {
            const recElement = document.getElementById('signal-recommendation');
            recElement.textContent = data.overall_analysis.recommendation;
            recElement.className = 'signal-recommendation ' + data.overall_analysis.recommendation.toLowerCase().replace(' ','');
            document.getElementById('signal-description').textContent = data.overall_analysis.commentary || '';
        } else {
            updateSignalRecommendation(data.fear_and_greed.score, spread);
        }

        // --- Header meta info ---
        const fngMetaEl = document.getElementById('fng-meta');
        if (fngMetaEl) {
            const tsRaw = Number(data.fear_and_greed.timestamp);
            if (!Number.isNaN(tsRaw) && tsRaw > 0) {
                const isoDate = new Date(tsRaw * 1000).toISOString().slice(0, 10);
                fngMetaEl.textContent = `Daily • ${isoDate}`;
            } else {
                fngMetaEl.textContent = "Daily";
            }
        }

        const aaiiMetaEl = document.getElementById('aaii-meta');
        if (aaiiMetaEl && data.aaii_sentiment.report_date) {
            aaiiMetaEl.textContent = `Weekly • ${data.aaii_sentiment.report_date}`;
        }

        const ssiMetaEl = document.getElementById('ssi-meta');
        if (ssiMetaEl && data.bank_of_america_ssi && data.bank_of_america_ssi.length > 0) {
            const latestSSI = data.bank_of_america_ssi[data.bank_of_america_ssi.length - 1];
            if (latestSSI.date) {
                ssiMetaEl.textContent = `Monthly • ${latestSSI.date}`;
            }
        }

        const overallMetaEl = document.getElementById('overall-meta');
        if (overallMetaEl) {
            const dates = [];
            const tsRaw = Number(data.fear_and_greed.timestamp);
            if (!Number.isNaN(tsRaw) && tsRaw > 0) dates.push(new Date(tsRaw * 1000));
            if (data.aaii_sentiment.report_date) {
                const d = new Date(data.aaii_sentiment.report_date);
                if (!isNaN(d)) dates.push(d);
            }
            if (dates.length) {
                const latestDate = dates.sort((a, b) => b - a)[0];
                overallMetaEl.textContent = latestDate.toISOString().slice(0, 10);
            } else {
                overallMetaEl.textContent = "";
            }
        }
    }

    // --- UI Rendering ---

    function renderFearGreed(fngData) {
        // Main display
        const valueEl = document.getElementById('fng-value');
        const ratingEl = document.getElementById('fng-rating');
        valueEl.textContent = Math.round(fngData.score);
        ratingEl.textContent = fngData.rating.toUpperCase();
        updateElementClass(valueEl, fngData.rating, ['fear-extreme', 'fear', 'neutral', 'greed', 'greed-extreme']);
        updateElementClass(ratingEl, fngData.rating, ['fear-extreme', 'fear', 'neutral', 'greed', 'greed-extreme']);

        // Main bar
        document.getElementById('fng-bar-fill').style.width = `${fngData.score}%`;
        document.getElementById('fng-bar-marker').style.left = `${fngData.score}%`;
        document.getElementById('fng-bar-fill').style.background = getFngBarColor(fngData.score);
        
        // Main commentary from cache (generated by LLM) or fallback
        const commentaryText = fngData.commentary && fngData.commentary.length > 0 ? fngData.commentary : "From this level, markets typically see mixed returns over next 30 days";
        document.getElementById('fng-main-stats').textContent = commentaryText;
        
        // Components - pass the historical time series data
        const componentsContainer = document.getElementById('fng-components');
        componentsContainer.innerHTML = fngData.components.map(c => renderComponentBar(c, fngData.historicalTimeSeries)).join('');

        // Historical data
        const historyContainer = document.getElementById('fng-history-table');
        historyContainer.innerHTML = renderFngHistory(fngData);
        document.getElementById('fng-summary').textContent = `Current: ${Math.round(fngData.score)} | 1W: ${Math.round(fngData.previous_1_week)} | 1M: ${Math.round(fngData.previous_1_month)}`;
    }

    function renderAaiiSentiment(data) {
        // Main display
        const bull = parseFloat(data.bullish);
        const bear = parseFloat(data.bearish);
        const neutral = parseFloat(data.neutral);
        const spread = bull - bear;

        const spreadEl = document.getElementById('aaii-spread-value');
        spreadEl.textContent = `${spread > 0 ? '+' : ''}${spread.toFixed(1)}%`;
        updateElementClass(spreadEl, getSentimentZone(spread), ['bullish', 'bearish', 'neutral']);
        document.getElementById('aaii-spread-label').className = `index-label ${getSentimentZone(spread)}`;
        
        // Main stats
        const aaiiCommentary = data.commentary && data.commentary.length > 0 ? data.commentary : "When spread near zero, markets often at inflection point";
        document.getElementById('aaii-main-stats').textContent = aaiiCommentary;

        // Segmented bar
        const total = bull + bear + neutral;
        
        const bearishEl = document.getElementById('aaii-bar-bearish');
        const neutralEl = document.getElementById('aaii-bar-neutral');
        const bullishEl = document.getElementById('aaii-bar-bullish');
        
        bearishEl.style.width = `${(bear/total)*100}%`;
        bearishEl.style.background = '#4169E1';

        neutralEl.style.left = `${(bear/total)*100}%`;
        neutralEl.style.width = `${(neutral/total)*100}%`;
        neutralEl.style.background = '#999';

        bullishEl.style.left = `${((bear+neutral)/total)*100}%`;
        bullishEl.style.width = `${(bull/total)*100}%`;
        bullishEl.style.background = '#FFB347';

        // Zone labels
        document.getElementById('aaii-label-bearish').innerHTML = `BEARISH<br>${bear.toFixed(1)}%`;
        document.getElementById('aaii-label-neutral').innerHTML = `NEUTRAL<br>${neutral.toFixed(1)}%`;
        document.getElementById('aaii-label-bullish').innerHTML = `BULLISH<br>${bull.toFixed(1)}%`;

        // Components
        const componentsContainer = document.getElementById('aaii-components');
        componentsContainer.innerHTML = renderAaiiComponents(data);

        // Historical table
        const historyContainer = document.getElementById('aaii-history-table');
        let historyRows = `<tr><td>Current</td><td>${spread > 0 ? '+' : ''}${spread.toFixed(1)}%</td><td>${bull.toFixed(1)}%</td><td>${bear.toFixed(1)}%</td><td class="${getSentimentZone(spread)}">${getSentimentZone(spread).toUpperCase()}</td></tr>`;
        
        // Add 1 week ago data if available
        if (data.historical && data.historical['1w_ago']) {
            const weekData = data.historical['1w_ago'];
            historyRows += `<tr><td>1W Ago</td><td>${weekData.spread > 0 ? '+' : ''}${weekData.spread}%</td><td>${weekData.bullish}%</td><td>${weekData.bearish}%</td><td class="${getSentimentZone(weekData.spread)}">${getSentimentZone(weekData.spread).toUpperCase()}</td></tr>`;
        } else {
            historyRows += `<tr><td>1W Ago</td><td>...</td><td>...</td><td>...</td><td>...</td></tr>`;
        }
        
        // Add 1 month ago data if available
        if (data.historical && data.historical['1m_ago']) {
            const monthData = data.historical['1m_ago'];
            historyRows += `<tr><td>1M Ago</td><td>${monthData.spread > 0 ? '+' : ''}${monthData.spread}%</td><td>${monthData.bullish}%</td><td>${monthData.bearish}%</td><td class="${getSentimentZone(monthData.spread)}">${getSentimentZone(monthData.spread).toUpperCase()}</td></tr>`;
        } else {
            historyRows += `<tr><td>1M Ago</td><td>...</td><td>...</td><td>...</td><td>...</td></tr>`;
        }
        
        historyContainer.innerHTML = historyRows;
        
        // Update 52-week summary with real statistics
        if (data.statistics_52w) {
            const stats = data.statistics_52w;
            document.getElementById('aaii-summary').textContent = `52W: ${stats.spread_min}% to ${stats.spread_max}% | Avg: ${stats.spread_avg}%`;
        } else {
            document.getElementById('aaii-summary').textContent = `52W: ... to ... | Avg: ...`;
        }
    }

    function renderSSI(ssiData) {
        if (!ssiData || !Array.isArray(ssiData) || ssiData.length === 0) {
            console.error("No SSI data available");
            return;
        }

        // Get the latest SSI value
        const latestSSI = ssiData[ssiData.length - 1];
        const ssiLevel = parseFloat(latestSSI.level);
        
        // Main display
        const valueEl = document.getElementById('ssi-value');
        const ratingEl = document.getElementById('ssi-rating');
        valueEl.textContent = `${ssiLevel.toFixed(1)}%`;
        
        // Determine SSI rating based on contrarian interpretation
        let rating, ratingClass;
        if (ssiLevel < 50) {
            rating = "BEARISH";
            ratingClass = "bearish";
        } else if (ssiLevel < 55) {
            rating = "NEUTRAL";
            ratingClass = "neutral";
        } else if (ssiLevel < 60) {
            rating = "BULLISH";
            ratingClass = "bullish";
        } else {
            rating = "EXTREME BULLISH";
            ratingClass = "extreme-bullish";
        }
        
        ratingEl.textContent = rating;
        updateElementClass(valueEl, ratingClass, ['bearish', 'neutral', 'bullish', 'extreme-bullish']);
        updateElementClass(ratingEl, ratingClass, ['bearish', 'neutral', 'bullish', 'extreme-bullish']);

        // Main bar (45-65% range with center at 55%)
        const minRange = 45;
        const maxRange = 65;
        const barPercentage = ((ssiLevel - minRange) / (maxRange - minRange)) * 100;
        const clampedBarPercentage = Math.max(0, Math.min(100, barPercentage));
        
        document.getElementById('ssi-bar-fill').style.width = `${clampedBarPercentage}%`;
        document.getElementById('ssi-bar-marker').style.left = `${clampedBarPercentage}%`;
        document.getElementById('ssi-bar-fill').style.background = getSSIBarColor(ssiLevel);
        
        // Main commentary - contrarian interpretation
        let commentary;
        if (ssiLevel >= 58) {
            commentary = `High allocation (${ssiLevel.toFixed(1)}%) suggests widespread bullishness. Contrarian signal for potential market top.`;
        } else if (ssiLevel <= 52) {
            commentary = `Low allocation (${ssiLevel.toFixed(1)}%) indicates widespread bearishness. Contrarian opportunity for market bottom.`;
        } else {
            commentary = `Moderate allocation (${ssiLevel.toFixed(1)}%) suggests balanced sentiment. Watch for extreme readings.`;
        }
        document.getElementById('ssi-main-stats').textContent = commentary;
        
        // Components - show recent monthly data
        const componentsContainer = document.getElementById('ssi-components');
        componentsContainer.innerHTML = renderSSIComponents(ssiData);

        // Historical table
        const historyContainer = document.getElementById('ssi-history-table');
        historyContainer.innerHTML = renderSSIHistory(ssiData);
        
        // Summary with 6-month range
        const recentData = ssiData.slice(-6); // Last 6 months
        const levels = recentData.map(d => parseFloat(d.level));
        const minLevel = Math.min(...levels);
        const maxLevel = Math.max(...levels);
        const avgLevel = levels.reduce((sum, val) => sum + val, 0) / levels.length;
        document.getElementById('ssi-summary').textContent = `6M: ${minLevel.toFixed(1)}% to ${maxLevel.toFixed(1)}% | Avg: ${avgLevel.toFixed(1)}%`;
    }

    function updateSignalRecommendation(fearGreedValue, bullBearSpread) {
        let recommendation = "HOLD";
        let description = "";
        
        fearGreedValue = Number(fearGreedValue);
        bullBearSpread = Number(bullBearSpread);
        
        // Original logic from mockup
        if (fearGreedValue >= 75 && bullBearSpread > 20) {
            recommendation = "SELL";
            description = "Extreme greed (F&G: " + fearGreedValue + ") combined with excessive bullishness (AAII: +" + bullBearSpread.toFixed(1) + "%) signals peak optimism. Strong contrarian sell signal as markets often correct from euphoric levels.";
        } else if (fearGreedValue < 25 && bullBearSpread < -20) {
            recommendation = "BUY";
            description = "Extreme fear (F&G: " + fearGreedValue + ") combined with excessive bearishness (AAII: " + bullBearSpread.toFixed(1) + "%) indicates capitulation. Strong contrarian buy signal as markets typically rebound from oversold conditions.";
        } else if (fearGreedValue >= 55 || bullBearSpread > 15) {
            recommendation = "HOLD";
            description = "Elevated greed levels suggest caution, but readings not extreme enough for contrarian action. Monitor for further deterioration in sentiment before considering defensive positions.";
        } else if (fearGreedValue < 45 || bullBearSpread < -15) {
            recommendation = "HOLD";
            description = "Fear is present but not at panic levels. Watch for extreme readings or capitulation signals before taking contrarian long positions.";
        } else {
            recommendation = "HOLD";
            description = "Fear & Greed at " + fearGreedValue + " ("+getFngRating(fearGreedValue)+") suggests mild complacency, while AAII spread near zero (+" + bullBearSpread.toFixed(1) + "%) indicates investor indecision. Mixed signals warrant caution - await clearer extremes in either indicator before taking contrarian positions.";
        }
        
        const recElement = document.getElementById('signal-recommendation');
        recElement.textContent = recommendation;
        recElement.className = 'signal-recommendation ' + recommendation.toLowerCase();
        
        document.getElementById('signal-description').textContent = description;
    }

    // --- Helpers ---
    
    function showLoading() {
        if (loadingIndicator) loadingIndicator.style.display = 'flex';
    }

    function hideLoading() {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
    
    function updateTimestamp() {
        const timestampEl = document.getElementById('timestamp');
        if (timestampEl) {
            const now = new Date();
            timestampEl.textContent = now.toISOString().replace('T', ' ').substring(0, 19) + ' ET';
        }
    }

    function getFngBarColor(value) {
        if (value < 25) return '#7B68EE'; // Extreme Fear
        if (value < 45) return '#4169E1'; // Fear
        if (value < 55) return '#999';    // Neutral
        if (value < 75) return '#FFB347'; // Greed
        return '#FF6B6B';                 // Extreme Greed
    }

    function getFngRating(value) {
        if (value < 25) return 'Extreme Fear';
        if (value < 45) return 'Fear';
        if (value < 55) return 'Neutral';
        if (value < 75) return 'Greed';
        return 'Extreme Greed';
    }

    function renderComponentBar(component, historicalTimeSeries) {
        const tooltips = {
            "Market Volatility": "VIX level relative to 50-day moving average - shows current volatility vs recent trend",
            "Put and Call Options": "Put/Call ratio - above 1.0 indicates defensive positioning (fear)",
            "Stock Price Momentum": "S&P 500 level relative to 125-day moving average - shows momentum vs long-term trend",
            "Junk Bond Demand": "Credit spread - narrow spreads indicate risk appetite (greed)",
            "Stock Price Breadth": "Advancing vs declining volume - positive shows broad participation",
            "Safe Haven Demand": "Bond vs stock performance - negative shows flight to safety",
            "Stock Price Strength": "52-week highs vs lows ratio - positive indicates strength"
        };
        
        // Shorter all-caps abbreviations
        const abbreviations = {
            "Market Volatility": "VIX",
            "Put and Call Options": "PUT/CALL",
            "Stock Price Momentum": "MOMENTUM",
            "Junk Bond Demand": "JUNK BOND",
            "Stock Price Breadth": "BREADTH",
            "Safe Haven Demand": "SAFE HAVEN",
            "Stock Price Strength": "PRICE STR"
        };
        
        // Get historical context and current value for this component using real API data
        const context = getComponentContext(component, historicalTimeSeries);
        const rating = component.rating.toLowerCase();
        const displayName = abbreviations[component.name] || component.name;
        const componentId = component.name.replace(/\s+/g, '-').toLowerCase();
        
        // Create center-based bar with real historical ranges
        const barWidth = 40;
        const centerBar = createFngCenterBarFromHistorical(context.currentValue, context.min, context.max, context.average);
        const barClass = context.currentValue >= context.average ? 'greed' : 'fear';
        
        // Calculate deviation from average
        const deviation = context.currentValue - context.average;
        let deviationFormatted;
        
        // Format deviation based on component type
        if (component.name === "Market Volatility") {
            deviationFormatted = deviation >= 0 ? `+${Math.abs(deviation).toFixed(1)}` : `-${Math.abs(deviation).toFixed(1)}`;
        } else if (component.name === "Put and Call Options") {
            deviationFormatted = deviation >= 0 ? `+${Math.abs(deviation).toFixed(2)}` : `-${Math.abs(deviation).toFixed(2)}`;
        } else if (component.name === "Stock Price Momentum") {
            deviationFormatted = deviation >= 0 ? `+${Math.abs(deviation).toFixed(0)}` : `-${Math.abs(deviation).toFixed(0)}`;
        } else {
            deviationFormatted = deviation >= 0 ? `+${Math.abs(deviation).toFixed(1)}` : `-${Math.abs(deviation).toFixed(1)}`;
        }
        
        // Enhanced tooltip with real range information
        const enhancedTooltip = `${tooltips[component.name] || ''} | Current: ${context.formattedCurrent} | 52W Range: ${context.formattedMin} to ${context.formattedMax} | Avg: ${context.formattedAvg}`;

        // Determine if this component uses a moving-average center (hard-coded list)
        const usesMovingAverage = (component.name === "Stock Price Momentum" || component.name === "Market Volatility");
        const centerLabel = usesMovingAverage ? 'CURRENT MA' : 'Average';
        const vsLabel = usesMovingAverage ? 'MA' : 'avg';

        const htmlResult = `
            <div class="bar-row expandable-bar" id="${componentId}" onclick="toggleBarExpansion('${componentId}')">
                <!-- Collapsed State -->
                <div class="bar-collapsed">
                    <span class="bar-label" title="${enhancedTooltip}">${displayName} <span class="zone-indicator ${rating}">◾${rating.substring(0,4).toUpperCase()}</span></span>
                    <span class="bar-chart ${barClass}">${centerBar}</span>
                    <span class="bar-value">${context.formattedCurrent}</span>
                </div>
                
                <!-- Expanded State -->
                <div class="bar-expanded" style="display: none;">
                    <div class="expanded-header">
                        <h3 class="component-title">${component.name}</h3>
                        <div class="current-reading">
                            <span class="reading-value">${context.formattedCurrent}</span>
                            <span class="vs-average">${deviationFormatted} vs ${vsLabel}</span>
                        </div>
                    </div>
                    
                    <div class="component-description">
                        ${tooltips[component.name] || ''}
                    </div>
                    
                    <div class="expanded-bar-container">
                        <span class="bar-chart-expanded ${barClass}">${centerBar}</span>
                    </div>
                    
                    <div class="range-labels">
                        <div class="range-left">
                            <div class="range-label">1Y Low</div>
                            <div class="range-value">${context.formattedMin}</div>
                        </div>
                        <div class="range-center">
                            <div class="range-label">${centerLabel}</div>
                            <div class="range-value">${context.formattedAvg}</div>
                        </div>
                        <div class="range-right">
                            <div class="range-label">1Y High</div>
                            <div class="range-value">${context.formattedMax}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return htmlResult;
    }
    
    // Helper function to create center-based bar using real historical data
    function createFngCenterBarFromHistorical(currentValue, minValue, maxValue, avgValue) {
        const barWidth = 40;
        const centerPos = Math.floor(barWidth / 2);
        
        // Calculate position within the historical range
        const range = maxValue - minValue;
        if (range === 0) {
            // If no variation in historical data, show at center
            return '░'.repeat(centerPos) + '|' + '░'.repeat(centerPos);
        }
        
        // Normalize current position relative to average (center = average)
        const avgPosition = centerPos; // Average is always at center
        const currentPosition = Math.round(((currentValue - avgValue) / (range / 2)) * centerPos + centerPos);
        const clampedPosition = Math.max(0, Math.min(barWidth - 1, currentPosition));
        
        let bar = '';
        for (let i = 0; i < barWidth; i++) {
            if (i === avgPosition) {
                bar += '|'; // Mark the average position
            } else if (currentValue < avgValue && i >= clampedPosition && i < avgPosition) {
                bar += '█'; // Fill between current and average (fear side)
            } else if (currentValue > avgValue && i > avgPosition && i <= clampedPosition) {
                bar += '█'; // Fill between average and current (greed side)
            } else {
                bar += '░'; // Empty space
            }
        }
        
        return bar;
    }
    
    // Helper function to get component context from real API historical data
    function getComponentContext(component, historicalTimeSeries) {
        if (!historicalTimeSeries) {
            // Fallback to simulated data if historicalTimeSeries not available
            return getSimulatedComponentContext(component);
        }
        
        // Map component names to API keys
        const apiKeyMap = {
            "Market Volatility": "market_volatility_vix",
            "Put and Call Options": "put_call_options", 
            "Stock Price Momentum": "market_momentum_sp500",
            "Junk Bond Demand": "junk_bond_demand",
            "Stock Price Breadth": "stock_price_breadth",
            "Safe Haven Demand": "safe_haven_demand",
            "Stock Price Strength": "stock_price_strength"
        };

        // Map components to their moving average center points
        const centerPointMap = {
            "Stock Price Momentum": "market_momentum_sp125", // 125-day MA
            "Market Volatility": "market_volatility_vix_50"  // 50-day MA
        };
        
        const apiKey = apiKeyMap[component.name];
        const componentData = historicalTimeSeries[apiKey];
        
        if (!componentData || !componentData.data || componentData.data.length === 0) {
            console.log(`⚠️ ${component.name} falling back to simulated data - no historical data found for ${apiKey}`);
            return getSimulatedComponentContext(component);
        }
        
        // Extract historical values from time series
        const historicalValues = componentData.data.map(point => point.y);
        const currentValue = historicalValues[historicalValues.length - 1]; // Most recent value
        
        // Calculate statistics
        const minValue = Math.min(...historicalValues);
        const maxValue = Math.max(...historicalValues);
        
        // For components with moving average center points, use the MA as center
        // For others, use historical average as center
        let avgValue;
        const centerKey = centerPointMap[component.name];
        
        if (centerKey && historicalTimeSeries[centerKey]) {
            // Use current moving average from the separate time series
            const maData = historicalTimeSeries[centerKey];
            if (maData.data && maData.data.length > 0) {
                // Get the most recent MA value
                avgValue = maData.data[maData.data.length - 1].y;
            } else {
                // Fallback to historical average
                avgValue = historicalValues.reduce((sum, val) => sum + val, 0) / historicalValues.length;
            }
        } else {
            // Use historical average as center for other components
            avgValue = historicalValues.reduce((sum, val) => sum + val, 0) / historicalValues.length;
        }
        
        // Format values based on component type
        const formatValue = (value) => {
            if (component.name === "Market Volatility") {
                return value.toFixed(1);
            } else if (component.name === "Put and Call Options") {
                return value.toFixed(2);
            } else if (component.name === "Junk Bond Demand") {
                return `${(value * 100).toFixed(0)}bps`;
            } else if (component.name === "Stock Price Momentum") {
                return value.toFixed(0);
            } else if (component.name === "Stock Price Breadth") {
                return value.toFixed(0);
            } else if (component.name === "Safe Haven Demand") {
                return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
            } else if (component.name === "Stock Price Strength") {
                return value.toFixed(2);
            }
            return value.toFixed(2);
        };
        
        return {
            currentValue: currentValue,
            min: minValue,
            max: maxValue,
            average: avgValue,
            formattedCurrent: formatValue(currentValue),
            formattedMin: formatValue(minValue),
            formattedMax: formatValue(maxValue),
            formattedAvg: formatValue(avgValue)
        };
    }
    
    // Fallback function for simulated data (when API data not available)
    function getSimulatedComponentContext(component) {
        const componentRanges = {
            "Market Volatility": { min: 12, max: 45, avg: 20 },
            "Put and Call Options": { min: 0.6, max: 1.4, avg: 0.9 },
            "Stock Price Momentum": { min: 4500, max: 6000, avg: 5250 },
            "Junk Bond Demand": { min: 1.2, max: 2.5, avg: 1.6 },
            "Stock Price Breadth": { min: 500, max: 1500, avg: 1000 },
            "Safe Haven Demand": { min: -5, max: 10, avg: 2 },
            "Stock Price Strength": { min: 0.5, max: 5, avg: 2 }
        };
        
        const range = componentRanges[component.name] || { min: 0, max: 100, avg: 50 };
        const currentValue = range.min + (component.score / 100) * (range.max - range.min);
        
        return {
            currentValue: currentValue,
            min: range.min,
            max: range.max,
            average: range.avg,
            formattedCurrent: currentValue.toFixed(1),
            formattedMin: range.min.toString(),
            formattedMax: range.max.toString(),
            formattedAvg: range.avg.toString()
        };
    }

    function renderFngHistory(fngData) {
        const historicals = [
            { timeframe: 'Current', score: Math.round(fngData.score), rating: getFngRating(fngData.score) },
            { timeframe: '1 Day Ago', score: Math.round(fngData.previous_close), rating: getFngRating(fngData.previous_close)},
            { timeframe: '1 Week Ago', score: Math.round(fngData.previous_1_week), rating: getFngRating(fngData.previous_1_week)},
            { timeframe: '1 Month Ago', score: Math.round(fngData.previous_1_month), rating: getFngRating(fngData.previous_1_month)},
            { timeframe: '1 Year Ago', score: Math.round(fngData.previous_1_year), rating: getFngRating(fngData.previous_1_year)},
        ];
        
        return historicals.map((row, i) => {
            let changeHtml = '-';
            if (i === 0 && fngData.score && fngData.previous_close) {
                 const change = Math.round(fngData.score - fngData.previous_close);
                 const changePct = (change / fngData.previous_close) * 100;
                 const changeClass = change > 0 ? 'positive' : 'negative';
                 changeHtml = `<span class="${changeClass}">${change > 0 ? '+' : ''}${change} (${changePct.toFixed(2)}%)</span>`;
            }

            const ratingClass = row.rating.toLowerCase().replace(' ', '-');
            return `
                <tr>
                    <td>${row.timeframe}</td>
                    <td class="${ratingClass}">${row.score}</td>
                    <td class="${ratingClass}">${row.rating.toUpperCase()}</td>
                    <td>${changeHtml}</td>
                </tr>
            `;
        }).join('');
    }

    function renderAaiiComponents(data) {
        const bull = parseFloat(data.bullish);
        const bear = parseFloat(data.bearish);
        const spread = bull - bear;

        const bullVsAvg = parseFloat(data.bull_vs_avg ?? 0);
        const bearVsAvg = parseFloat(data.bear_vs_avg ?? 0);
        const spreadVsAvg = parseFloat(data.spread_vs_avg ?? 0);

        const barWidth = 40;
        
        // ----------------
        // Build expandable components using 52-week stats attached in the cache
        // ----------------
        const stats = data.statistics_52w || {};

        // Helper to build a single expandable AAII bar component
        function buildAaiiComponent(config) {
            const {
                id,
                label,
                currentValue,
                min,
                max,
                avg,
                deviation,
                barClass,
                tooltip
            } = config;

            const centerBar = createFngCenterBarFromHistorical(currentValue, min, max, avg);
            const deviationFormatted = `${deviation > 0 ? '+' : ''}${Math.abs(deviation).toFixed(1)}pp`;

            return `
                <div class="bar-row expandable-bar" id="${id}" onclick="toggleBarExpansion('${id}')">
                    <!-- Collapsed -->
                    <div class="bar-collapsed">
                        <span class="bar-label" title="${tooltip}">${label}</span>
                        <span class="bar-chart ${barClass}">${centerBar}</span>
                        <span class="bar-value">${currentValue.toFixed(1)}%</span>
                    </div>
                    <!-- Expanded -->
                    <div class="bar-expanded" style="display:none;">
                        <div class="expanded-header">
                            <h3 class="component-title">${label}</h3>
                            <div class="current-reading">
                                <span class="reading-value">${currentValue.toFixed(1)}%</span>
                                <span class="vs-average">${deviationFormatted} vs AVG</span>
                            </div>
                        </div>
                        <div class="component-description">${tooltip}</div>
                        <div class="expanded-bar-container">
                            <span class="bar-chart-expanded ${barClass}">${centerBar}</span>
                        </div>
                        <div class="range-labels">
                            <div class="range-left"><div class="range-label">1Y LOW</div><div class="range-value">${min.toFixed(1)}%</div></div>
                            <div class="range-center"><div class="range-label">AVERAGE</div><div class="range-value">${avg.toFixed(1)}%</div></div>
                            <div class="range-right"><div class="range-label">1Y HIGH</div><div class="range-value">${max.toFixed(1)}%</div></div>
                        </div>
                    </div>
                </div>
            `;
        }

        const componentsHtml = [];

        // Bullish component
        componentsHtml.push(buildAaiiComponent({
            id: 'aaii-bullish',
            label: 'BULL %',
            currentValue: bull,
            min: stats.bull_min ?? bull,
            max: stats.bull_max ?? bull,
            avg: stats.bull_avg ?? bull,
            deviation: bullVsAvg,
            barClass: bull >= (stats.bull_avg ?? bull) ? 'greed' : 'fear',
            tooltip: `Current bullish percentage vs 52-week distribution (avg ${stats.bull_avg ?? '-'}%)`
        }));

        // Bearish component
        componentsHtml.push(buildAaiiComponent({
            id: 'aaii-bearish',
            label: 'BEAR %',
            currentValue: bear,
            min: stats.bear_min ?? bear,
            max: stats.bear_max ?? bear,
            avg: stats.bear_avg ?? bear,
            deviation: bearVsAvg,
            barClass: bear >= (stats.bear_avg ?? bear) ? 'fear' : 'greed', // higher bearish -> fear
            tooltip: `Current bearish percentage vs 52-week distribution (avg ${stats.bear_avg ?? '-'}%)`
        }));

        // Spread component (Bull ‑ Bear)
        componentsHtml.push(buildAaiiComponent({
            id: 'aaii-spread',
            label: 'SPREAD',
            currentValue: spread,
            min: stats.spread_min ?? spread,
            max: stats.spread_max ?? spread,
            avg: stats.spread_avg ?? spread,
            deviation: spreadVsAvg,
            barClass: spread >= (stats.spread_avg ?? spread) ? 'greed' : 'fear',
            tooltip: `Bull-Bear spread vs 52-week distribution (avg ${stats.spread_avg ?? '-'}pp)`
        }));

        return componentsHtml.join('');
    }
    
    function updateElementClass(element, rating, classes) {
        element.classList.remove(...classes);
        const cls = rating.toLowerCase().replace(/ /g, '-');
        if (classes.includes(cls)) {
            element.classList.add(cls);
        } else {
            element.classList.add('neutral');
        }
    }

    function getSentimentZone(spread) {
        if (spread > 10) return 'bullish';
        if (spread < -10) return 'bearish';
        return 'neutral';
    }

    function getSSIBarColor(value) {
        if (value < 50) return '#4169E1'; // Bearish (blue)
        if (value < 55) return '#999';    // Neutral (gray)
        if (value < 60) return '#FFB347'; // Bullish (orange)
        return '#FF6B6B';                 // Extreme Bullish (red)
    }

    function renderSSIComponents(ssiData) {
        // Show recent 6 months as simple monthly evolution list
        const recentData = ssiData.slice(-6).reverse(); // Most recent first
        
        return recentData.map((dataPoint, index) => {
            const level = parseFloat(dataPoint.level);
            const monthYear = dataPoint.date;
            const confidence = dataPoint.confidence || 'medium';
            
            // Determine sentiment zone
            let sentimentZone;
            if (level < 50) sentimentZone = 'bearish';
            else if (level < 55) sentimentZone = 'neutral';
            else if (level < 60) sentimentZone = 'bullish';
            else sentimentZone = 'extreme-bullish';
            
            const displayLabel = index === 0 ? 'LATEST' : `${index}M AGO`;
            const confidenceIndicator = confidence === 'high' ? '●' : confidence === 'medium' ? '◐' : '○';
            
            // Calculate change from previous month if available
            let changeIndicator = '';
            if (index < recentData.length - 1) {
                const previousLevel = parseFloat(recentData[index + 1].level);
                const change = level - previousLevel;
                if (Math.abs(change) >= 0.1) {
                    changeIndicator = change > 0 ? ' ↗' : ' ↘';
                }
            }
            
            return `
                <div class="ssi-month-row">
                    <span class="ssi-month-label">${displayLabel} ${monthYear}</span>
                    <span class="ssi-month-value ${sentimentZone}">${level.toFixed(1)}%${changeIndicator}</span>
                    <span class="confidence-indicator" title="Confidence: ${confidence}">${confidenceIndicator}</span>
                </div>
            `;
        }).join('');
    }

    function renderSSIHistory(ssiData) {
        // Show recent 6 months in table format
        const recentData = ssiData.slice(-6).reverse(); // Most recent first
        
        return recentData.map((dataPoint, index) => {
            const level = parseFloat(dataPoint.level);
            let sentimentZone;
            if (level < 50) sentimentZone = 'bearish';
            else if (level < 55) sentimentZone = 'neutral';
            else if (level < 60) sentimentZone = 'bullish';
            else sentimentZone = 'extreme-bullish';
            
            const sentimentText = sentimentZone.replace('-', ' ').toUpperCase();
            const confidenceText = (dataPoint.confidence || 'medium').toUpperCase();
            
            return `
                <tr>
                    <td>${dataPoint.date}</td>
                    <td class="${sentimentZone}">${level.toFixed(1)}%</td>
                    <td class="${sentimentZone}">${sentimentText}</td>
                    <td>${confidenceText}</td>
                </tr>
            `;
        }).join('');
    }

    // Toggle bar expansion for Fear & Greed components
    window.toggleBarExpansion = function(componentId) {
        const barRow = document.getElementById(componentId);
        if (!barRow) return;
        
        const collapsed = barRow.querySelector('.bar-collapsed');
        const expanded = barRow.querySelector('.bar-expanded');
        
        if (collapsed.style.display === 'none') {
            // Currently expanded, collapse it
            collapsed.style.display = 'flex';
            expanded.style.display = 'none';
            barRow.classList.remove('expanded');
        } else {
            // Currently collapsed, expand it
            collapsed.style.display = 'none';
            expanded.style.display = 'block';
            barRow.classList.add('expanded');
            

        }
    }

    // Toggle bar expansion for Fear & Greed components
    function toggleBarExpansion(componentId) {
        const barRow = document.getElementById(componentId);
        if (!barRow) return;
        
        const collapsed = barRow.querySelector('.bar-collapsed');
        const expanded = barRow.querySelector('.bar-expanded');
        
        if (collapsed.style.display === 'none') {
            // Currently expanded, collapse it
            collapsed.style.display = 'flex';
            expanded.style.display = 'none';
            barRow.classList.remove('expanded');
        } else {
            // Currently collapsed, expand it
            collapsed.style.display = 'none';
            expanded.style.display = 'block';
            barRow.classList.add('expanded');
        }
    }

    // Read more functionality
    function initializeReadMore() {
        // Target signal descriptions, component descriptions, and main stats
        const descriptions = document.querySelectorAll('.signal-description, .component-description, .main-stats');
        console.log('Found descriptions:', descriptions.length);
        
        descriptions.forEach((description, index) => {
            const text = description.textContent.trim();
            console.log(`Description ${index} length:`, text.length, 'chars');
            
            // Check if text is longer than ~200 characters (roughly 3 lines)
            if (text.length > 200) {
                console.log('Adding read more to description', index);
                
                const words = text.split(' ');
                // Use 25 words on mobile, 30 on desktop
                const isMobile = window.innerWidth < 768;
                const wordLimit = isMobile ? 25 : 30;
                const truncatedText = words.slice(0, wordLimit).join(' ');
                const fullText = text;
                
                // Create read more link
                const readMoreLink = document.createElement('span');
                readMoreLink.innerHTML = ' <span class="read-more-link">read more</span>';
                readMoreLink.style.cursor = 'pointer';
                
                // Create read less link
                const readLessLink = document.createElement('span');
                readLessLink.innerHTML = ' <span class="read-more-link">read less</span>';
                readLessLink.style.cursor = 'pointer';
                
                // Set up initial truncated state with inline read more
                description.innerHTML = truncatedText;
                description.appendChild(readMoreLink);
                
                // Add click handlers
                readMoreLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('Read more clicked');
                    description.innerHTML = fullText;
                    description.appendChild(readLessLink);
                });
                
                readLessLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('Read less clicked');
                    description.innerHTML = truncatedText;
                    description.appendChild(readMoreLink);
                });
            }
        });
    }

    // --- Init ---
    initDashboard();
}); 