<template>
  <div class="results">
    <h1>
      Downloaded Files
    </h1>
    <div style="text-align:center;">
      <table align="center" border="1">
          <tr>
              <th>Name</th>
              <th>Size</th>
          </tr>
          <tr>
              <td>Batma Begins.torrent</td>
              <td>4.0 GB</td>
          </tr>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SharedFiles',
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
