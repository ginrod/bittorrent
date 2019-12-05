<template>
  <div class="index">
    <h1>{{ msg }}</h1>
    <div>
    <input v-model="pattern" placeholder="Search">
         <!-- <button type="button" class="btn btn-default btn-sm" style="background-color:green"> -->
         <button style="background-color:green; color:white">
           Go</button>
      <!-- <div style="-webkit-transform: rotate(45deg); 
               -moz-transform: rotate(45deg); 
                 -o-transform: rotate(45deg);
                    transform: rotate(45deg);">
              &#9906;
          </div> -->
      </div>
    <h3>Download Settings</h3>
    <ul>
      <li><input type="file" webkitdirectory directory multiple/></li>
      <li><a href="https://github.com/vuejs/vue-cli/tree/dev/packages/%40vue/cli-plugin-eslint" target="_blank" rel="noopener">History</a></li>
      <li><a href="/shared-files" target="_blank" rel="noopener">Shared Files</a></li>
    </ul>
    <h3>Downloading Progress</h3>
    <ul></ul>
    <div style="text-align:center;">
      <table align="center" border="1">
          <tr>
              <th>File name</th>
              <th>Downloading</th>
              <th></th>
              <th></th>
          </tr>
          <tr>
              <td>Dummy1</td>
              <td>Yes</td>
              <td>Pause</td>
              <td>Cancel</td>
          </tr>
          <tr>
              <td>The Lion King</td>
              <td>No</td>
              <td>100%</td>
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
  </div>
</template>

<script>
export default {
  name: 'Index',
  props: {
    msg: String,
    pattern: String
  }
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
