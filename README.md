# **Proportional Streamflow Disaggregation Using Precipitation and Land Cover in disjoint hydrologic and hydraulic networks**

For testing disaggregation methods, the following data sets and transformations were used.

## **Data:** 

### 1.  **Hydrofabric:** 

A hydrofabric (flowines, divides, flowpaths) was subset from the experimental v3.0 fabric at nwis gageID: '01183500'. 

![](https://lh7-rt.googleusercontent.com/docsz/AD_4nXeK23UBp1RGs1vxwXNtmvXDujh_iEj0nLlYspjEdAC9HH2IPTQG0x0qq4XRFfLueN0lHd72VF8C8HqK4dWtx9iOtgQGSSnRYVOfh0_gIkcMdRw29GRwaUnm_7vQPCsMY_fKjDjaP93PGCur2AU867k?key=XBKcXvbG-URTFFoiG1slFA)

### 2.  **Streamflow**

Daily streamflow data from ['2023-01-01'] to ['2023-12-31'] from the USGS were used for testing.

### 3.  **USGS National Land Cover Dataset (NLCD)**

|  |  |  |  |  |
|---------------|---------------|---------------|---------------|---------------|
| **Description** | **Anderson Level 1** | **Anderson Level 2** | **Level 1** **Runoff Coefficient** | **Level 2Runoff Coefficient** |
| Open Water  | 1 | 11 | 0.95 | 0.95 |
| Perennial Ice/Snow | 1 | 12 | 0.95 | 0.9 |
| Developed Open Space | 2 | 21 | 0.875 | 0.2 |
| Developed Low Intensity | 2 | 22 | 0.875 | 0.5 |
| Developed Medium Intensity | 2 | 23 | 0.875 | 0.75 |
| Developed High Intensity | 2 | 24 | 0.875 | 0.9 |
| Barren Land | 3 | 31 | 0.075 | 0.1 |
| Deciduous Forest | 4 | 41 | 0.2 | 0.2 |
| Evergreen forest | 4 | 42 | 0.2 | 0.25 |
| Mixed forest | 4 | 43 | 0.2 | 0.22 |
| Shrub/Scrub | 5 | 52 | 0.175 | 0.18 |
| Grassland | 7 | 71 | 0.175 | 0.35 |
| Pasture | 8 | 81 | 0.4 | 0.4 |
| Crops | 8 | 82 | 0.4 | 0.45 |
| Woody Wetlands | 9 | 90 | 0.125 | 0.15 |
| Herbaceous Wetlands | 9 | 95 | 0.125 | 0.1 |

### 4.  **Precipitation data:** 

Average daily surface precipitation data (from Daymet 2023) was summarized to the incremental area of the hydrofabric.

### 5. **Soil Data:** 

30m POLARIS data was used to summarize average saturated hydraulic conductivity per incremental area in the hydrofabric.

## **Methods**

### **Incremental divides approach:** 

These methods disaggregate discharge with respect to the target incremental divide and not total upstream drainage.

#### **1. Area method**

$$
Qi(t) = Q_{nexus(t)} * \frac{A_i}{max(Aj)_j}
$$

where j iterates through all flowlines in the watershed.

#### **2. Area + Landcover based runoff coefficient:** 

$$
Qi(t) = Q_{nexus(t)} * \frac{A_i * Y_i}{max(A * Y)_j}
$$

Where:

-   $Q_{i(t)}$: Estimated flow from incremental area i at time

-   $Q_{nexus(t)}$: Observed or forecasted flow

-   $A_i$: Area of incremental areaa i

-   $C_i$: Runoff yield modifier, based on land cover in i where

$$
Y_i = \sum_{l=1}^{L} f_{i,l} * y_l
$$

and

-   $f_{i,l}$: Fraction of land class lll in catchment i

-   $y_l$​: Runoff yield factor for land cover l, derived from long-term studies (in mm/day or normalized scale)

#### **3. Area + Landcover based runoff coefficient + average rainfall**

$$
Qi(t) = Q_{nexus(t)} * \frac{A_i * Y_i * P_i}{max(A * Y * C)_j}
$$

Where:

-   $Q_{nexus(t)}$: streamflow at nexus (e.g., from NWM or observations)

-   $A_i$: area of catchment i (km²)

-   $P_i$: precipitation annual sum at catchment i

-   $Y_i$: **effective runoff coefficient** for catchment i

#### **4. Area + Landcover based runoff coefficient + average rainfall + hydraulic conductivity**

$$
Qi(t) = Q_{nexus(t)} * \frac{A_i * \frac{1}{K_i} * P_i * Y_i}{max(A * \frac{1}{K} * Y)_j}
$$

Where:

-   $K_i$: Average hydraulic conductivity at catchment

#### **5.  Area + Landcover based runoff coefficient + “realtime” rainfall + hydraulic conductivity**

Qi(t) = Qnexus(t) \* Aiɑ \* 1/Ki⍵\*Pi(t)Ɣ \* Ciβmax((Aɑ \* 1/K⍵\* P(t)Ɣ\*Cβ)j)

$$
Qi(t) = Q_{nexus(t)} * \frac{A^ɑ_i * \frac{1}{K^⍵_i} * P_i(t)^Ɣ * Y^β_i}{max(A^ɑ * \frac{1}{K^⍵} * P(t)^Ɣ * Y^β)_j}
$$

Where:

-   $P_i(t)$: precipitation at catchment i, time t (mm)

Also one can determine the degree of contribution of each through optimization using ɑ, β, ⍵, Ɣ parameters that range between 0-1. For example in watershed where runoff is dominated by rapid, event-based surface flow calibration would prioritize increasing Ɣ (precipitation)  and β(runoff coefficient) to amplify model ‘s response to storm magnitude and surface imperviousness. Conversely, in a system dominated by groundwater and sustained baseflow, optimization would focus on increasing ⍵ (hydraulic conductivity) and  ɑ (cumulative area) to emphasize the role of subsurface infiltration and storage in attenuating flood peaks and maintaining flow during dry periods.

Note: we have kept all values of the parameters to 1 and did not perform the optimization.

### **6-10. Methods 1-5 are repeated using total drainage area (DA) in place of incremental area (A)**

### **11. Drainage Area with travel time** 

This method disaggregates discharge with respect to the target total drainage area considering travel time through manning’s equation. Here we used most complex models involving K, P, C, and CA and incorporated travel time into calculation of flow disaggregation using manning’s equation: 

$$
T = sum(\frac{L}{\frac{1}{n} * R_h^\frac{2}{3} * S^\frac{1}{2}})
$$

$$
Q_{i, t} = Q_{nexus(t+T_i)} * W_i
$$

Where T is total travel time of a reach and W is the weight from the combination of K, P, C, and DA

### **12. Cumulative Area with travel time + seasonal precipitation:** 

This methods adds seasonal  precipitation weights (isolated to 2023). 

$$
P_{seasonal(i,s)} = \sum_{d in s} P_{daily(i, d)}
$$

where:

$P_{seasonal(i, s)}$ is the total precipitation for flowline i during season s.

$s$ represents one of the four seasons (e.g., 'Summer').

The summation Σ runs over all days d that fall within the season s.

$P_daily(i, d)$ is the daily precipitation for flowline i on day d.

$$
Unnormalized_{W_{i,s}} = \frac{A_i* Y_i * P_{seasonal_{i, s}}}{K_i}
$$

$$
{W_{seasonal_{(i,s)}}} = \frac{Unnormalized_{W_{i,s}}}{\sum_j Unnormalized_{W_{i,s}}}
$$

### **13. Cumulative Area with travel time + real time precipitation weights:**

Here, precipitation weights are calculated on a daily (timestep of streamflow) basis reflecting contributions of precipitation to total discharge on that particular date for target areas.

$$
Unnormalized_{W_{i,s}} = \frac{A_i * Y_i * P_{effective_{(i,d)}}}{K_i}
$$

$$
P_{effective_{(i,d)}} = \\
P_{(i,d)} if P_{(i,d)} > 0 \\
PRECIP_FLOOR if P_{(i,d)} = 0
$$

## **Results:**

Of the Incremental area approaches the best performing was…

\
\

This method provided the most accurate estimate across all, by accounting for:

1.  Captures Real-Time Storm Dynamics: By using daily precipitation, the model is event-driven, not based on static averages. Unlike area-only methods, it correctly concentrates the disaggregated flow in the specific sub-basins that actually received rain, providing a physically realistic response to weather events.

2.  Models True River Drainage: It calculates the water travel time from every upstream segment to the watershed outlet. This allows it to correctly lag the discharge, ensuring that runoff generated on a specific day is accurately matched to its later arrival and measurement at the outlet, which is crucial for modeling flood timing.

3.  Provides a Proportional Flow Distribution: The model is robust and adapts to changing conditions. On storm days, flow is proportionally assigned based on rainfall intensity. During dry periods, it seamlessly transitions to distributing baseflow based on physical properties like area and soil type.

4.  Ensures Continuous Downstream Flow Aggregation: By using the cumulative drainage area (the total area upstream of a divide) in its weighting formula, the model guarantees that calculated discharge realistically increases as you move downstream. 
