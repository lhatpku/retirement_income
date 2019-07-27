Survey
    .StylesManager
    .applyTheme("default");

var json = {
    "completeText": "Finish",
    "pageNextText": "Continue",
    "pagePrevText": "Previous"
};


var page0 = {
    "elements": [
        {
            "type": "panel",
            "elements": [
                {
                    "type": "html",
                    "name": "tool_intro",
                    "html": "<article class='intro'>  <h1 class='intro__heading intro__heading--income title' style='color:grey'>        Spending Budget Survey        </h1>       <div class='intro__body wysiwyg'>    <p> In this section, you will be asked about your periodical spending (weekly, monthly or annually) for different items.</p>    <p>The tool will automatically group your spendings to essential and discretionary buckets and calculate your retirement goals </p>    </div>     </article>"
                }
            ],
            "name": "panel1"
        }
    ],
    "name": "page0"
};

var essential_spending_list = 
[
    {
        "name": "house",
        "title": "Housing Essentials",
        "bucket_list": [
            {
                "name": "rent",
                "title": "Rent and/or mortage with property taxes",
                "default_fre": "Monthly"
            },
            {
                "name": "utility",
                "title": "Utilities (water, gas, electricity, etc.)",
                "default_fre": "Monthly"
            }
        ]
    },
    {
        "name": "transportation",
        "title": "Transportation Daily Commute Essentials",
        "bucket_list": [
            {
                "name": "public",
                "title": "Public Transportion - Train, Bus, Taxi, Other",
                "default_fre": "Daily"
            },
            {
                "name": "private",
                "title": "Private Vehicles - Depreciation/Lease and Services & Repairs",
                "default_fre": "Annually"
            }
        ]
    },
    {
        "name": "digital",
        "title": "Digital Services Essentials",
        "bucket_list": [
            {
                "name": "basic",
                "title": "Internet, Phone, TV",
                "default_fre": "Monthly"
            },
            {
                "name": "other",
                "title": "Other Subscriptions",
                "default_fre": "Monthly"
            }
        ]
    },
    {
        "name": "living",
        "title": "Food and Other Basic Living Essentials",
        "bucket_list": [
            {
                "name": "grocery",
                "title": "Groceries and Household supplies",
                "default_fre": "Monthly"
            },
            {
                "name": "clothing",
                "title": "Clothing",
                "default_fre": "Monthly"
            },
            {
                "name": "other",
                "title": "Other",
                "default_fre": "Monthly"
            }
        ]
    },
    {
        "name": "health",
        "title": "Health Essential Expenditures & Provisions",
        "bucket_list": [
            {
                "name": "standard",
                "title": "Out-of-pocket standard healthcare costs (insurance, medications, etc.)",
                "default_fre": "Monthly"
            },
            {
                "name": "additional",
                "title": "Additional out-of-pocket non-standard costs (e.g., long-term care, surgery)",
                "default_fre": "Monthly"
            }
        ]
    }
];

var freedom_spending_list = 
[
    {
        "name": "entertainment",
        "title": "Entertainment",
        "bucket_list": [
            {
                "name": "restaurant",
                "title": "Restaurants & Drinks",
                "default_fre": "Monthly"
            },
            {
                "name": "event",
                "title": "Events (sports, music, theather etc.)",
                "default_fre": "Monthly"
            }
        ]
    },
    {
        "name": "shopping",
        "title": "Shopping",
        "bucket_list": [
            {
                "name": "electronics",
                "title": "Electronics and home goods (computer, phone, appliances)",
                "default_fre": "Annually"
            },
            {
                "name": "luxury",
                "title": "Luxury Items (clothes, jewellery)",
                "default_fre": "Monthly"
            }
        ]
    },
    {
        "name": "vacation",
        "title": "Vacation and non-standard Travel",
        "bucket_list": [
            {
                "name": "Flights",
                "title": "Flights",
                "default_fre": "Monthly"
            },
            {
                "name": "Lodge",
                "title": "Lodging: hotels, airbnb, etc",
                "default_fre": "Monthly"
            }
        ]
    }
];

var essential_group_list = essential_spending_list.map(d => d.name);
var freedom_group_list = freedom_spending_list.map(d => d.name);

const mapToElementLower = function(bucket) {

    return {
        "type": "panel",
        "name": bucket["name"],
        "title": bucket["title"],
        "elements": [
            {
                "type": "text",
                "inputType": "number",
                "name": "amount_"+bucket["name"],
                "title": "Spending Amount",
                "defaultValue":0
            }, {
                "type": "dropdown",
                "name": "frequency_"+bucket["name"],
                "title": "Spending Frequency",
                "startWithNewLine": false,
                "defaultValue": bucket["default_fre"],
                "choices": ["Daily","Weekly","Monthly", "Annually"]
            }
        ]
    };
};

const mapToElementHigher = function(panel) {

    var bucket_element_list = panel["bucket_list"].map(d => mapToElementLower(d));

    return panel_element = {
        "type": "paneldynamic",
        "renderMode": "progressTop",
        "allowAddPanel": false,
        "allowRemovePanel": false,
        "name": panel["name"],
        "title": panel["title"],
        "panelCount": 1,    
        "templateElements":bucket_element_list
    };
        
};

var page1 = {
    "name": "page1",
    "elements": [
        {
            "type":"panel",
            "name": "essential",
            "title": "Essential Spending",
            "elements":essential_spending_list.map(d => mapToElementHigher(d))
        }
    ]
};

var page2 = {
    "name": "page1",
    "elements": [
        {
            "type":"panel",
            "name": "essential",
            "title": "Essential Spending",
            "elements":freedom_spending_list.map(d => mapToElementHigher(d))
        }
    ]
};


var pages = [page0,page1,page2];

json["pages"] = pages;

// Add the function to extract result data
const calcTotalSpend = function(data) {

    var essential_cost = 0;
    var freedom_cost = 0;

    for (var key1 in data) {
        if (data.hasOwnProperty(key1)) {
            var group_budget = data[key1][0];
            for (var key2 in group_budget) {
                if (key2.split('_')[0] === 'amount') {
                    var freq_key = 'frequency_'+key2.split('_')[1];
                    var freq_value = group_budget[freq_key];
                    var num_period;
                    ["Daily","Weekly","Monthly", "Annually"]
                    switch (freq_value) {
                        case 'Daily':
                            num_period = 365;
                            break;
                        case 'Weekly':
                            num_period = 52;
                            break;
                        case 'Monthly':
                            num_period = 12;
                            break;
                        case 'Annually':
                            num_period = 1;
                    };
                    if (essential_group_list.includes(key1)) {
                        essential_cost = essential_cost + num_period * group_budget[key2];
                    }
                    else {
                        freedom_cost = freedom_cost + num_period * group_budget[key2];
                    };
                }
            }
        }
    }

    var cost = {};
    cost['freedom'] = freedom_cost;
    cost['essential'] = essential_cost;
    cost['total'] = freedom_cost + essential_cost;

    return cost

};

// Add the survey
var modal = document.getElementById("survey");

$("#open-survey").on('click',function(event){

    modal.style.display = "block";

    window.survey = new Survey.Model(json);

    survey
        .onComplete
        .add(function (result) {
            
            var cost = calcTotalSpend(result.data);
            var target = parseFloat($('.take-home-income').first().text());

            var ratio_1 = Math.round(cost.essential/target * 100);
            var ratio_2 = Math.round(cost.total/target * 100);

            $('#replacement-ratio-1').attr('value',ratio_1);
            $('#replacement-ratio-2').attr('value', ratio_2);

            $('#non-dis-spend').text(Math.round(parseFloat(target) * ratio_1 / 100));
            $('#dis-spend').text(Math.round(parseFloat(target) * ratio_2 / 100));

            $('#replacement-ratio-1').trigger('change');
            $('#replacement-ratio-2').trigger('change');

        });


    $("#surveyElement").Survey({model: survey});;

    window.onclick = function(event) {
        if (event.target == modal) {
          modal.style.display = "none";
        }
    };
    
});


