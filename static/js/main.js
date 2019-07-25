function wealth_plot(data,percentile) {

  Highcharts.chart('wealth-plot', {
    chart: {
      type: 'area'
    },
    title: {
      text: 'Wealth Projection'
    },
    xAxis: {
      title: {
        text: 'Age'
      },
      allowDecimals: false,
      labels: {
        formatter: function () {
          return this.value; 
        }
      }
    },
    yAxis: {
      title: {
        text: 'Wealth'
      },
      labels: {
        formatter: function () {
          return this.value / 1000 + 'k';
        }
      }
    },
    tooltip: {
      pointFormat: 'Wealth-{series.name} at age <b>{point.x}</b><br/>is {point.y:,.0f}'
    },
    plotOptions: {
      area: {
        pointStart: data.Age[0],
        marker: {
          enabled: false,
          symbol: 'circle',
          radius: 2,
          states: {
            hover: {
              enabled: true
            }
          }
        }
      }
    },
    series: [{
      name: percentile.toString()+'%',
      data: data.Wealth.filter(d => d.percentile === percentile).map(d => d.wealth)[0]
    }]
  });

};

function income_plot(data,percentile) {

  income_start_index = data.profile.income_start_index;
  income_vector = data.Income.filter(d => d.percentile === percentile).map(d => d.income)[0].slice(income_start_index);
  age_vector = data.Age.slice(income_start_index);
  target_upper = data.target_upperBound.slice(income_start_index);
  target_lower = data.target_lowerBound.slice(income_start_index);

  income_plot_series = _.zip(age_vector,income_vector);
  boundary_plot_series = _.zip(age_vector,target_lower,target_upper);

  // console.log(income_plot_series);
  // console.log(boundary_plot_series);

  Highcharts.chart('income-plot', {

    title: {
      text: 'Income Projection'
    },
  
    xAxis: {
      title: {
        text: 'Age'
      },
      allowDecimals: false,
      labels: {
        formatter: function () {
          return this.value; 
        }
      }
    },
  
    yAxis: {
      title: {
        text: 'Wealth'
      },
      labels: {
        formatter: function () {
          return this.value / 1000 + 'k';
        }
      }
    },
  
    tooltip: {
      pointFormat: 'Income-{series.name} at age <b>{point.x}</b><br/>is {point.y:,.0f}'
    },
  
    legend: {
    },
  
    series: [{
      name: percentile.toString()+'%',
      data: income_plot_series,
      zIndex: 1,
      marker: {
        fillColor: 'white',
        lineWidth: 2,
        lineColor: Highcharts.getOptions().colors[0]
      }
    }, {
      name: 'Boundary',
      data: boundary_plot_series,
      type: 'arearange',
      lineWidth: 0,
      linkedTo: ':previous',
      color: Highcharts.getOptions().colors[0],
      fillOpacity: 0.3,
      zIndex: 0,
      marker: {
        enabled: false
      }
    }]
  });
};

function port_plot(data,age) {
  // Splice in transparent for the center circle
// Highcharts.getOptions().colors.splice(0, 0, 'transparent');


Highcharts.chart('portfolio-advice-plot', {

  chart: {
    height: '100%'
  },

  title: {
    text: 'Portfolio Allocation'
  },
 
  series: [{
    type: "sunburst",
    data: data[age],
    allowDrillToNode: true,
    cursor: 'pointer',
    dataLabels: {
      format: '{point.name}',
      filter: {
        property: 'innerArcLength',
        operator: '>',
        value: 16
      }
    },
    levels: [{
      level: 1,
      levelIsConstant: false,
      dataLabels: {
        filter: {
          property: 'outerArcLength',
          operator: '>',
          value: 64
        }
      }
    }, 
    {
      level: 2,
      colorVariation: {
        key: 'brightness',
        to: -1.5
      }
    }, {
      level: 3,
      colorVariation: {
        key: 'brightness',
        to: 0.5
      }
    }]

  }],
  tooltip: {
    headerFormat: "",
    pointFormat: 'The Allocation of <b>{point.name}</b> is <b>{point.value}</b>'
  }
});

}


$(document).ready(function(){

  $('#plan-demo').hide();
  $('#plan-loader').hide();

  var rangeSlider = document.getElementById('portfolio-advice-slider');
  noUiSlider.create(rangeSlider, {
      start: 30,
      step: 1,
      range: {
          'min': 30,
          'max': 91
      }
  });

  $('#submit').on('click',function(event){

    rangeSlider.noUiSlider.updateOptions({
      start: parseInt($('#age').val()),
      range: {
          'min': parseInt($('#age').val()),
          'max': parseInt($('#spend-down-age').text())
      }
    });

    $('#plan-demo').hide();
    $('#plan-loader').fadeIn();

    $.ajax({
      data: {
        name: $('#name').val(),
        age: parseInt($('#age').val()),
        gender: $('#gender option:selected').text(),
        salary: parseFloat($('#salary').val()),
        retirement_age: parseInt($('#retirement-age').val()),
        manageable_balance: parseFloat($('#account-1-balance').val()),
        manageable_contrib: parseFloat($('#account-1-contribution').val()),
        manageable_tax: $('#account-1-tax option:selected').text(),
        ss_claim_age: parseInt($('#ss-claim-age').val()),
        ss_benefit: parseFloat($('#ss-benefit').val()),
        annuity_start_age: parseInt($('#annuity-start-age').val()),
        annuity_benefit: parseFloat($('#annuity-benefit').val()),
        non_dis_target: parseFloat($('#non-dis-spend').text()),
        dis_target: parseFloat($('#dis-spend').text()),
        spend_down_age: parseInt($('#spend-down-age').text()),
        minimum_spending_ratio: parseFloat($('#min-spending-ratio-output').text()),
        spending_strategy:$('#spending-strategy').dropdown('get text')
        // spending_strategy: $('#spending-strategy').find(':selected').text()
      },
      type: 'POST',
      url: '/process'

    })
    .done(function(data) {

      $('#plan-loader').fadeOut();
      $('#plan-demo').fadeIn();

      wealth_plot(data,30);
      income_plot(data,30);
      port_plot(data.portfolio,parseInt($('#age').val()));

      var rangeSliderValueElement = document.getElementById('portfolio-advice-age');
      rangeSlider.noUiSlider.on('update', function (values, handle) {
        var age_Output = parseFloat(values[handle]).toFixed(0)
        rangeSliderValueElement.innerHTML = `<span><strong>Age</strong>: ${age_Output}</span>`;
        port_plot(data.portfolio,String(age_Output));
      });

      $('input:radio[name="percentile"]').change(function() {
        wealth_plot(data,parseFloat($(this).val()));
        income_plot(data,parseFloat($(this).val()));
      })

    });
  });
});
