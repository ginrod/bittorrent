<template>
  <div class="shared-files">
    <h1>
      Shared Files
    </h1>

    <div style="text-align:center;">
      <table align="center" border="1">
          <tr>
              <th>Name</th>
              <th>Extension</th>
              <th>Size</th>
          </tr>
          <tr>
              <td>Dummy1</td>
              <td>Yes</td>
              <td>1.0 GB</td>
          </tr>
          <tr>
              <td>The Lion King</td>
              <td>No</td>
              <td>300 MB</td>
          </tr>
          <tr>
              <td>Dummy2</td>
              <td>Yes</td>
              <td>0%</td>
          </tr>
          <tr>
              <td>Dummy2 Largooooooooooooooooooooooooooooooooooooooooo</td>
              <td>Yes</td>
              <td>0%</td>
          </tr>
          <tr>
              <td>Dummy2</td>
              <td>Yes</td>
              <td>0%</td>
          </tr>
          <tr>
              <td>Dummy2</td>
              <td>Yes</td>
              <td>0%</td>
          </tr>
          <tr>
              <td>Dummy2</td>
              <td>Yes</td>
              <td>0%</td>
          </tr>
      </table>
    </div>

    <ul></ul>
    <button type="button" class="btn btn-default btn-sm" style="background-color:green; color:white">Share New File</button>
    <!-- <button style="background-color:white;">Share New File</button> -->

  </div>
</template>

<script>
export default {
  name: 'SharedFiles',
  props: {
    msg: String,
    pattern: String
  },
  mounted() {
      fetch("http://192.168.1.104:5001/downloading").then(function (response) {
        return response.json();})
        .then(function (result) {
          this.downloding_list =  result;
          alert(this.downloding_list)   
    });
    },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
