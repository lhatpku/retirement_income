$('#salary,#ss-claim-age').change(function(event){

  $.ajax({
    data: {
      salary: $('#salary').val(),
      claim_age: $('#ss-claim-age').val(),
    },
    type: 'POST',
    url: '/social_security'

  })
  .done(function(data) {

    if (data.error) {

    }
    else {

      // console.log(data.social_security_benefit);

      $('#ss-benefit').attr('value', data.social_security_benefit);
    }

  });

});
