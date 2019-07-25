var slideInput = document.querySelector("#spending-min-ratio");


function drawSpendingCurve (x_1,x_2,t_1,t_2,alpha_) {
    // set the dimensions and margins of the graph
    var margin = {top: 10, right: 30, bottom: 20, left: 80},
    width = 580 - margin.left - margin.right,
    height = 240 - margin.top - margin.bottom;

    // append the svg object to the body of the page
    var svg = d3.select("#spending-curve")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform",
      "translate(" + margin.left + "," + margin.top + ")");

    // var x_1 = parseInt($('#retirement-age').val());
    // var x_2 = parseInt($('#spend-down-age').text());
    var a_param = 1/Math.pow((x_1-x_2)/2,2);
    var age_array = Array.from(Array(x_2-x_1+1),(x,index) => index + x_1);

    // add the x Axis
    var x = d3.scaleLinear()
    .domain([x_1, x_2])
    .range([0, width]);

    svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x));

    // add the y Axis
    var y = d3.scaleLinear()
    .range([height, 0])
    .domain([0, t_2]);

    svg.append("g")
    .call(d3.axisLeft(y));

    // Calc Spending Curve Function and Update Curve 
    function calcSpendingCurve(age,alpha_) {
    
        var a = (1-alpha_) * a_param;
        var b = alpha_;
    
        return a * Math.pow((age-(x_1+x_2)/2),2) + b;
    }

    // Calculate the initial input values
    // d3.select("#spending-min-ratio").property("value", "1");
    d3.select("#min-spending-ratio-output").text(alpha_*100);
    var age_ratio_array_init_1 = age_array.map(d => [d,t_1 * calcSpendingCurve(d,alpha_)]);
    var age_ratio_array_init_2 = age_array.map(d => [d,t_2 * calcSpendingCurve(d,alpha_)]);

    var curve_1 = svg
    .append('g')
    .append("path")
      .attr("class", "mypath")
      .datum(age_ratio_array_init_1)
      .attr("fill", "none")
      .attr("opacity", ".8")
      .attr("stroke", "#76787A")
      .attr("stroke-width", 4)
      .attr("stroke-linejoin", "round")
      .attr("d",  d3.line()
        .curve(d3.curveBasis)
          .x(function(d) { return x(d[0]); })
          .y(function(d) { return y(d[1]); })
    );

    var curve_2 = svg
    .append('g')
    .append("path")
      .attr("class", "mypath")
      .datum(age_ratio_array_init_2)
      .attr("fill", "none")
      .attr("opacity", ".8")
      .attr("stroke", "#2CABFF")
      .attr("stroke-width", 4)
      .attr("stroke-linejoin", "round")
      .attr("d",  d3.line()
        .curve(d3.curveBasis)
          .x(function(d) { return x(d[0]); })
          .y(function(d) { return y(d[1]); })
    );

    function updateCurve(alpha_) {
        // recompute density estimation
        var age_ratio_array_1 = age_array.map(d => [d,t_1 * calcSpendingCurve(d,alpha_)]);
        var age_ratio_array_2 = age_array.map(d => [d,t_2 * calcSpendingCurve(d,alpha_)]);
        // update the chart
        curve_1
        .datum(age_ratio_array_1)
        .transition()
        .duration(1000)
        .attr("d",  d3.line()
            .curve(d3.curveBasis)
            .x(function(d) { return x(d[0]); })
            .y(function(d) { return y(d[1]); })
        );

        curve_2
        .datum(age_ratio_array_2)
        .transition()
        .duration(1000)
        .attr("d",  d3.line()
            .curve(d3.curveBasis)
            .x(function(d) { return x(d[0]); })
            .y(function(d) { return y(d[1]); })
        );
    }

    slideInput.addEventListener('input',function(event) {
        var selectedValue = parseFloat(slideInput.value);
        d3.select("#min-spending-ratio-output").text(Math.round(selectedValue*100));
        updateCurve(selectedValue);
    },false);
}

var age_1 = parseInt($('#retirement-age').val());
var age_2 = parseInt($('#spend-down-age').text());

var target_1 = parseInt($('#non-dis-spend').text());
var target_2 = parseInt($('#dis-spend').text());

drawSpendingCurve (age_1,age_2,target_1,target_2,1);

$('#salary,#account-1-contribution,#account-1-tax,#replacement-ratio-1,#replacement-ratio-2,#spend-down-confidence,#gender,#age,#retirement-age').change(function(event){

    $.ajax({
        data: {
          salary: $('#salary').val(),
          contribution: $('#account-1-contribution').val(),
          tax: $('#account-1-tax option:selected').text(),
          replacement_1: $('#replacement-ratio-1').val(),
          replacement_2: $('#replacement-ratio-2').val(),
          confidence_level:$('#spend-down-confidence').val(),
          gender:$('#gender option:selected').text(),
          age: $('#age').val()
        },
        type: 'POST',
        url: '/spendcurve'
  
      })
      .done(function(data) {
  
        if (data.error) {
  
        }
        else {
  
            d3.select("#spending-curve").selectAll("svg").remove();
            var target_update_1 = Math.round(data.target_1);
            var target_update_2 = Math.round(data.target_2);

            var age_update_1 = parseInt($('#retirement-age').val());
            var age_update_2 = parseInt(data.spend_down_age);
            var alpha = parseFloat(slideInput.value);

            drawSpendingCurve (age_update_1,age_update_2,target_update_1,target_update_2,alpha);
        }
  
    });
  
});

