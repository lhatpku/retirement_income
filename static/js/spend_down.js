$('#spend-down-confidence,#gender,#age').change(function(event){

  $.ajax({
    data: {
      confidence_level:$('#spend-down-confidence').val(),
      gender:$('#gender option:selected').text(),
      age: $('#age').val(),
    },
    type: 'POST',
    url: '/spenddown'

  })
  .done(function(data) {

    if (data.error) {

    }
    else {

      $('#spend-down-age').text(data.spend_down_age);
    }

  });

});
