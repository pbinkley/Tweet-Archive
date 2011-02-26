<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
   exclude-result-prefixes="xd"
   version="1.0">
   <xd:doc scope="stylesheet">
      <xd:desc>
         <xd:p><xd:b>Created on:</xd:b> Jan 16, 2011</xd:p>
         <xd:p><xd:b>Author:</xd:b> peterbinkley</xd:p>
         <xd:p></xd:p>
      </xd:desc>
   </xd:doc>
   <xsl:output method="html" encoding="utf-8"/>
   
   <!-- month: 2011-02 -->
   <xsl:param name="month"/>
   <!-- twitterId: pabinkley -->
   <xsl:param name="twitterID"/>
   <!-- timestampFetch -->
   <xsl:param name="timestampFetch"/>
   
   <xsl:variable name="title"><xsl:value-of select="$twitterID"/> tweets of <xsl:value-of select="$month"/></xsl:variable>
   <!-- timestamp_fetch="2011-01-17 08:45:44-0700" -->
   <!-- create a version of timestamp for use in file name: replace space and colon with dash, remove second and timezone -->
   <xsl:variable name="ts" select="substring(translate(/tweetarchive/statuses[@list='user_timeline']/@timestamp_fetch, ' :', '-'), 1, 17)"/>
   
   <xsl:key name="status-by-id" match="status | direct_message" use="id"/>
   <xsl:key name="status-by-replied-to-id" match="status | direct_message" use="in_reply_to_status_id"/>
   
   <xsl:template match="/">
      <html>
         <head>
            <title><xsl:value-of select="$title"/></title>
         </head>
         <style type="text/css">
<![CDATA[
.status {
   margin-top: 1em;
}
.reply {
   margin-left: 4em;
}
.other {
   margin-top: 1em;
   margin-left: 2em;
   background-color: #ccc;
}
.message {
   border: 1px solid red;
}
.lastupdate {
   font-style: italic; 
   font-size: 75%;
}
.replycount {
   font-style: italic; 
   margin-left: 2em;
}
.replycount:before {
   content: "» ";
}
]]>         </style>
         <body>
            <h1>
               <xsl:value-of select="$title"/>
            </h1>
            <p class="lastupdate">Last update: <xsl:value-of select="$timestampFetch"/></p>

            <xsl:apply-templates select="//status | //direct_message">
               <xsl:sort select="@timestamp" data-type="text"/>
            </xsl:apply-templates>

         </body>
      </html>
   </xsl:template>
   
   <xsl:template match="status | direct_message">
      <div>
         <xsl:attribute name="class">
            <xsl:choose>
               <xsl:when test="(user/screen_name = $twitterID or sender/screen_name = $twitterID) and in_reply_to_status_id != ''">status reply</xsl:when>
               <xsl:when test="user/screen_name = $twitterID or sender/screen_name = $twitterID">status</xsl:when>
               <xsl:otherwise>other</xsl:otherwise>
            </xsl:choose>
            <xsl:if test="name() = 'direct_message'"> message</xsl:if>
         </xsl:attribute>
         <xsl:value-of select="position()"/>
         <xsl:text>. </xsl:text>
         <xsl:value-of select="text"/>
         <br/>
         <xsl:apply-templates select="user | sender"/>
         <xsl:apply-templates select="recipient" mode="inline"/>
         <xsl:value-of select="created_at"/>
         <xsl:text> </xsl:text>
         <xsl:value-of select="id"/>
         <xsl:apply-templates select="in_reply_to_status_id[. != '']"/>

         <xsl:variable name="replycount" select="count(key('status-by-replied-to-id', id))"/>
         <xsl:if test="$replycount &gt; 0">
            <br/>
            <span class="replycount">
               <xsl:value-of select="$replycount"/>
               <xsl:text> </xsl:text>
               <xsl:choose>
                  <xsl:when test="$replycount = 1">reply</xsl:when>
                  <xsl:otherwise>replies</xsl:otherwise>
               </xsl:choose>
               <xsl:text> this month</xsl:text>
            </span>
         </xsl:if>
      </div>
   </xsl:template>
   
   <xsl:template match="in_reply_to_status_id">
      <xsl:text> - reply to </xsl:text>
      <xsl:apply-templates select="key('status-by-id', .)" mode="in-reply-to"/>
   </xsl:template>
   
   <xsl:template match="user | sender | recipient">
      <xsl:value-of select="screen_name"/>
      <xsl:text> (</xsl:text>
      <xsl:value-of select="name"/>
      <xsl:text>) </xsl:text>
   </xsl:template>
   
   <xsl:template match="recipient" mode="inline">
      <xsl:text> to </xsl:text>
      <xsl:apply-templates select="."/>
   </xsl:template>
   
   <xsl:template match="status | direct_message" mode="in-reply-to">
      <span class="in-reply-to">
         <xsl:value-of select="id"/>
         <xsl:text> [</xsl:text>
         <xsl:apply-templates select="user"/>
         <xsl:apply-templates select="recipient" mode="inline"/>
         <xsl:value-of select="created_at"/>
         <xsl:text>]</xsl:text>
      </span>
   </xsl:template>
</xsl:stylesheet>