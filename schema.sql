-- Dump of Lightroom Catalog schema - as of 8/28/2024
-- This is for reference only, and should not be used directly.

CREATE TABLE Adobe_AdditionalMetadata (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    additionalInfoSet INTEGER NOT NULL DEFAULT 0,
    embeddedXmp INTEGER NOT NULL DEFAULT 0,
    externalXmpIsDirty INTEGER NOT NULL DEFAULT 0,
    image INTEGER,
    incrementalWhiteBalance INTEGER NOT NULL DEFAULT 0,
    internalXmpDigest,
    isRawFile INTEGER NOT NULL DEFAULT 0,
    lastSynchronizedHash,
    lastSynchronizedTimestamp NOT NULL DEFAULT -63113817600,
    metadataPresetID,
    metadataVersion,
    monochrome INTEGER NOT NULL DEFAULT 0,
    xmp NOT NULL DEFAULT ''
)
CREATE TABLE Adobe_faceProperties (
    id_local INTEGER PRIMARY KEY,
    face INTEGER,
    propertiesString
)
CREATE TABLE Adobe_imageDevelopBeforeSettings (
    id_local INTEGER PRIMARY KEY,
    beforeDigest,
    beforeHasDevelopAdjustments,
    beforePresetID,
    beforeText,
    developSettings INTEGER,
    hasBigData INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE Adobe_imageDevelopSettings (
    id_local INTEGER PRIMARY KEY,
    allowFastRender INTEGER,
    beforeSettingsIDCache,
    croppedHeight,
    croppedWidth,
    digest,
    fileHeight,
    fileWidth,
    grayscale INTEGER,
    hasAIMasks INTEGER NOT NULL DEFAULT 0,
    hasBigData INTEGER NOT NULL DEFAULT 0,
    hasDevelopAdjustments INTEGER,
    hasDevelopAdjustmentsEx,
    hasLensBlur INTEGER NOT NULL DEFAULT 0,
    hasMasks INTEGER NOT NULL DEFAULT 0,
    hasPointColor INTEGER NOT NULL DEFAULT 0,
    hasRetouch,
    hasSettings1,
    hasSettings2,
    historySettingsID,
    image INTEGER,
    isHdrEditMode INTEGER NOT NULL DEFAULT 0,
    processVersion,
    profileCorrections,
    removeChromaticAberration,
    settingsID,
    snapshotID,
    text,
    validatedForVersion,
    whiteBalance
)
CREATE TABLE Adobe_imageProofSettings (
    id_local INTEGER PRIMARY KEY,
    colorProfile,
    image INTEGER,
    renderingIntent
)
CREATE TABLE Adobe_imageProperties (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    image INTEGER,
    propertiesString
)
CREATE TABLE Adobe_images (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    aspectRatioCache NOT NULL DEFAULT -1,
    bitDepth NOT NULL DEFAULT 0,
    captureTime,
    colorChannels NOT NULL DEFAULT 0,
    colorLabels NOT NULL DEFAULT '',
    colorMode NOT NULL DEFAULT -1,
    copyCreationTime NOT NULL DEFAULT -63113817600,
    copyName,
    copyReason,
    developSettingsIDCache,
    editLock INTEGER NOT NULL DEFAULT 0,
    fileFormat NOT NULL DEFAULT 'unset',
    fileHeight,
    fileWidth,
    hasMissingSidecars INTEGER,
    masterImage INTEGER,
    orientation,
    originalCaptureTime,
    originalRootEntity INTEGER,
    panningDistanceH,
    panningDistanceV,
    pick NOT NULL DEFAULT 0,
    positionInFolder NOT NULL DEFAULT 'z',
    propertiesCache,
    pyramidIDCache,
    rating,
    rootFile INTEGER NOT NULL DEFAULT 0,
    sidecarStatus,
    touchCount NOT NULL DEFAULT 0,
    touchTime NOT NULL DEFAULT 0
)
CREATE TABLE Adobe_libraryImageDevelop3DLUTColorTable (
    id_local INTEGER PRIMARY KEY,
    LUTFullString,
    LUTHash UNIQUE
)
CREATE TABLE Adobe_libraryImageDevelopHistoryStep (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    dateCreated,
    digest,
    hasBigData INTEGER NOT NULL DEFAULT 0,
    hasDevelopAdjustments,
    image INTEGER,
    name,
    relValueString,
    text,
    valueString
)
CREATE TABLE Adobe_libraryImageDevelopSnapshot (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    digest,
    hasBigData INTEGER NOT NULL DEFAULT 0,
    hasDevelopAdjustments,
    image INTEGER,
    locked,
    name,
    snapshotID,
    text
)
CREATE TABLE Adobe_libraryImageFaceProcessHistory (
    id_local INTEGER PRIMARY KEY,
    image INTEGER NOT NULL DEFAULT 0,
    lastFaceDetector,
    lastFaceRecognizer,
    lastImageIndexer,
    lastImageOrientation,
    lastTryStatus,
    userTouched
)
CREATE TABLE Adobe_namedIdentityPlate (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    description,
    identityPlate,
    identityPlateHash,
    moduleFont,
    moduleSelectedTextColor,
    moduleTextColor
)
CREATE TABLE Adobe_variables (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    name,
    value
)
CREATE TABLE Adobe_variablesTable (
	    id_local INTEGER PRIMARY KEY,
	    id_global UNIQUE NOT NULL,
	    name,
	    type,
	    value NOT NULL DEFAULT ''
	)
CREATE TABLE AgDNGProxyInfo (
    id_local INTEGER PRIMARY KEY,
    fileUUID NOT NULL DEFAULT '',
    status NOT NULL DEFAULT 'U',
    statusDateTime NOT NULL DEFAULT 0
)
CREATE TABLE AgDNGProxyInfoUpdater (
    id_local INTEGER PRIMARY KEY,
    taskID UNIQUE NOT NULL DEFAULT '',
    taskStatus NOT NULL DEFAULT 'pending',
    whenPosted NOT NULL DEFAULT ''
)
CREATE TABLE AgDeletedOzAlbumAssetIds(
	id_local NOT NULL DEFAULT 0,
	ozCatalogId NOT NULL,
	ozAlbumAssetId NOT NULL,
	changeCounter DEFAULT 0,
	lastSyncedChangeCounter DEFAULT 0
)
CREATE TABLE AgDeletedOzAlbumIds(
	id_local NOT NULL DEFAULT 0,
	ozCatalogId NOT NULL,
	ozAlbumId NOT NULL,
	changeCounter DEFAULT 0,
	lastSyncedChangeCounter DEFAULT 0
)
CREATE TABLE AgDeletedOzAssetIds(
	id_local NOT NULL DEFAULT 0,
	ozCatalogId NOT NULL,
	ozAssetId NOT NULL,
	changeCounter DEFAULT 0,
	lastSyncedChangeCounter DEFAULT 0
)
CREATE TABLE AgDeletedOzSpaceIds(
	id_local NOT NULL DEFAULT 0,
	ozCatalogId NOT NULL,
	ozSpaceId NOT NULL,
	changeCounter default 0,
	lastSyncedChangeCounter DEFAULT 0
)
CREATE TABLE AgDevelopAdditionalMetadata (
    id_local INTEGER PRIMARY KEY,
    caiAuthenticationInfo,
    hasDepthMap INTEGER,
    hasEnhance,
    image INTEGER
)
CREATE TABLE AgFolderContent (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    containingFolder INTEGER NOT NULL DEFAULT 0,
    content,
    name,
    owningModule
)
CREATE TABLE AgHarvestedDNGMetadata (
    id_local INTEGER PRIMARY KEY,
    image INTEGER,
    hasFastLoadData INTEGER,
    hasLossyCompression INTEGER,
    isDNG INTEGER,
    isHDR INTEGER,
    isPano INTEGER,
    isReducedResolution INTEGER
)
CREATE TABLE AgHarvestedExifMetadata (
    id_local INTEGER PRIMARY KEY,
    image INTEGER,
    aperture,
    cameraModelRef INTEGER,
    cameraSNRef INTEGER,
    dateDay,
    dateMonth,
    dateYear,
    flashFired INTEGER,
    focalLength,
    gpsLatitude,
    gpsLongitude,
    gpsSequence NOT NULL DEFAULT 0,
    hasGPS INTEGER,
    isoSpeedRating,
    lensRef INTEGER,
    shutterSpeed
)
CREATE TABLE AgHarvestedIptcMetadata (
    id_local INTEGER PRIMARY KEY,
    image INTEGER,
    cityRef INTEGER,
    copyrightState INTEGER,
    countryRef INTEGER,
    creatorRef INTEGER,
    isoCountryCodeRef INTEGER,
    jobIdentifierRef INTEGER,
    locationDataOrigination NOT NULL DEFAULT 'unset',
    locationGPSSequence NOT NULL DEFAULT -1,
    locationRef INTEGER,
    stateRef INTEGER
)
CREATE TABLE AgHarvestedMetadataWorklist (
    id_local INTEGER PRIMARY KEY,
    taskID UNIQUE NOT NULL DEFAULT '',
    taskStatus NOT NULL DEFAULT 'pending',
    whenPosted NOT NULL DEFAULT ''
)
CREATE TABLE AgInternedExifCameraModel (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedExifCameraSN (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedExifLens (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedIptcCity (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedIptcCountry (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedIptcCreator (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedIptcIsoCountryCode (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedIptcJobIdentifier (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedIptcLocation (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgInternedIptcState (
    id_local INTEGER PRIMARY KEY,
    searchIndex,
    value
)
CREATE TABLE AgLastCatalogExport ( image INTEGER PRIMARY KEY )
CREATE TABLE AgLibraryCollection (
    id_local INTEGER PRIMARY KEY,
    creationId NOT NULL DEFAULT '',
    genealogy NOT NULL DEFAULT '',
    imageCount,
    name NOT NULL DEFAULT '',
    parent INTEGER,
    systemOnly NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryCollectionChangeCounter(
	collection PRIMARY KEY,
	changeCounter DEFAULT 0,
	lastSyncedChangeCounter DEFAULT 0
)
CREATE TABLE AgLibraryCollectionContent (
    id_local INTEGER PRIMARY KEY,
    collection INTEGER NOT NULL DEFAULT 0,
    content,
    owningModule
)
CREATE TABLE AgLibraryCollectionCoverImage(
	id_local NOT NULL DEFAULT 0,
	collection PRIMARY KEY,
	collectionImage NOT NULL
)
CREATE TABLE AgLibraryCollectionImage (
    id_local INTEGER PRIMARY KEY,
    collection INTEGER NOT NULL DEFAULT 0,
    image INTEGER NOT NULL DEFAULT 0,
    pick NOT NULL DEFAULT 0,
    positionInCollection
)
CREATE TABLE AgLibraryCollectionImageChangeCounter(
	collectionImage PRIMARY KEY,
	collection NOT NULL,
	image NOT NULL,
	changeCounter DEFAULT 0,
	lastSyncedChangeCounter DEFAULT 0
)
CREATE TABLE AgLibraryCollectionImageOzAlbumAssetIds(
	id_local NOT NULL DEFAULT 0,
	collectionImage NOT NULL,
	collection NOT NULL,
	image NOT NULL,
	ozCatalogId NOT NULL,
	ozAlbumAssetId DEFAULT "pending"
)
CREATE TABLE AgLibraryCollectionImageOzSortOrder(
	collectionImage  PRIMARY KEY,
	collection NOT NULL,
	positionInCollection NOT NULL,
	ozSortOrder NOT NULL
)
CREATE TABLE AgLibraryCollectionLabel (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    collection INTEGER NOT NULL DEFAULT 0,
    label,
    labelData,
    labelGenerics,
    labelType NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryCollectionOzAlbumIds(
	id_local NOT NULL DEFAULT 0,
	collection NOT NULL,
	ozCatalogId NOT NULL,
	ozAlbumId DEFAULT "pending"
)
CREATE TABLE AgLibraryCollectionStack (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    collapsed INTEGER NOT NULL DEFAULT 0,
    collection INTEGER NOT NULL DEFAULT 0,
    text NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryCollectionStackData(
    stack INTEGER,
    collection INTEGER NOT NULL DEFAULT 0,
    stackCount INTEGER NOT NULL DEFAULT 0,
    stackParent INTEGER
)
CREATE TABLE AgLibraryCollectionStackImage (
    id_local INTEGER PRIMARY KEY,
    collapsed INTEGER NOT NULL DEFAULT 0,
    collection INTEGER NOT NULL DEFAULT 0,
    image INTEGER NOT NULL DEFAULT 0,
    position NOT NULL DEFAULT '',
    stack INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgLibraryCollectionSyncedAlbumData(
	collection NOT NULL,
	payloadKey NOT NULL,
	payloadData NOT NULL
)
CREATE TABLE AgLibraryCollectionTrackedAssets (
	collection NOT NULL,
	ozCatalogId DEFAULT "current"
)
CREATE TABLE AgLibraryFace (
    id_local INTEGER PRIMARY KEY,
    bl_x,
    bl_y,
    br_x,
    br_y,
    cluster INTEGER,
    compatibleVersion,
    ignored INTEGER,
    image INTEGER NOT NULL DEFAULT 0,
    imageOrientation NOT NULL DEFAULT '',
    orientation,
    origination NOT NULL DEFAULT 0,
    propertiesCache,
    regionType NOT NULL DEFAULT 0,
    skipSuggestion INTEGER,
    tl_x NOT NULL DEFAULT '',
    tl_y NOT NULL DEFAULT '',
    touchCount NOT NULL DEFAULT 0,
    touchTime NOT NULL DEFAULT -63113817600,
    tr_x,
    tr_y,
    version
)
CREATE TABLE AgLibraryFaceCluster (
    id_local INTEGER PRIMARY KEY,
    keyFace INTEGER
)
CREATE TABLE AgLibraryFaceData (
    id_local INTEGER PRIMARY KEY,
    data,
    face INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgLibraryFile (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    baseName NOT NULL DEFAULT '',
    errorMessage,
    errorTime,
    extension NOT NULL DEFAULT '',
    externalModTime,
    folder INTEGER NOT NULL DEFAULT 0,
    idx_filename NOT NULL DEFAULT '',
    importHash,
    lc_idx_filename NOT NULL DEFAULT '',
    lc_idx_filenameExtension NOT NULL DEFAULT '',
    md5,
    modTime,
    originalFilename NOT NULL DEFAULT '',
    sidecarExtensions
)
CREATE TABLE AgLibraryFileAssetMetadata(
	fileId PRIMARY KEY,
	sha256 NOT NULL,
	fileSize DEFAULT 0
)
CREATE TABLE AgLibraryFolder (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    parentId INTEGER,
    pathFromRoot NOT NULL DEFAULT '',
    rootFolder INTEGER NOT NULL DEFAULT 0,
    visibility INTEGER
)
CREATE TABLE AgLibraryFolderFavorite (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    favorite,
    folder INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgLibraryFolderLabel (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    folder INTEGER NOT NULL DEFAULT 0,
    label,
    labelData,
    labelGenerics,
    labelType NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryFolderStack (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    collapsed INTEGER NOT NULL DEFAULT 0,
    text NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryFolderStackData (
    stack INTEGER,
    stackCount INTEGER NOT NULL DEFAULT 0,
    stackParent INTEGER
)
CREATE TABLE AgLibraryFolderStackImage (
    id_local INTEGER PRIMARY KEY,
    collapsed INTEGER NOT NULL DEFAULT 0,
    image INTEGER NOT NULL DEFAULT 0,
    position NOT NULL DEFAULT '',
    stack INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgLibraryIPTC (
    id_local INTEGER PRIMARY KEY,
    altTextAccessibility,
    caption,
    copyright,
    extDescrAccessibility,
    image INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgLibraryImageAttributes (
    id_local INTEGER PRIMARY KEY,
    image INTEGER NOT NULL DEFAULT 0,
    lastExportTimestamp DEFAULT 0,
    lastPublishTimestamp DEFAULT 0
)
CREATE TABLE AgLibraryImageChangeCounter(
	image PRIMARY KEY,
	changeCounter DEFAULT 0,
	lastSyncedChangeCounter DEFAULT 0,
	changedAtTime DEFAULT '',
	localTimeOffsetSecs DEFAULT 0
)
CREATE TABLE AgLibraryImageOzAssetIds(
	id_local NOT NULL DEFAULT 0,
	image NOT NULL,
	ozCatalogId NOT NULL,
	ozAssetId DEFAULT "pending",
	ownedByCatalog DEFAULT 'Y'
)
CREATE TABLE AgLibraryImageSaveXMP (
    id_local INTEGER PRIMARY KEY,
    taskID UNIQUE NOT NULL DEFAULT '',
    taskStatus NOT NULL DEFAULT 'pending',
    whenPosted NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryImageSearchData (
    id_local INTEGER PRIMARY KEY,
    featInfo,
    height,
    idDesc,
    idDescCh,
    image INTEGER NOT NULL DEFAULT 0,
    width
)
CREATE TABLE AgLibraryImageSyncedAssetData (
	image NOT NULL,
	payloadKey NOT NULL,
	payloadData NOT NULL
)
CREATE TABLE AgLibraryImageXMPUpdater (
    id_local INTEGER PRIMARY KEY,
    taskID UNIQUE NOT NULL DEFAULT '',
    taskStatus NOT NULL DEFAULT 'pending',
    whenPosted NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryImport (
    id_local INTEGER PRIMARY KEY,
    imageCount,
    importDate NOT NULL DEFAULT '',
    name
)
CREATE TABLE AgLibraryImportImage (
    id_local INTEGER PRIMARY KEY,
    image INTEGER NOT NULL DEFAULT 0,
    import INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgLibraryKeyword (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    dateCreated NOT NULL DEFAULT '',
    genealogy NOT NULL DEFAULT '',
    imageCountCache DEFAULT -1,
    includeOnExport INTEGER NOT NULL DEFAULT 1,
    includeParents INTEGER NOT NULL DEFAULT 1,
    includeSynonyms INTEGER NOT NULL DEFAULT 1,
    keywordType,
    lastApplied,
    lc_name,
    name,
    parent INTEGER
)
CREATE TABLE AgLibraryKeywordCooccurrence (
    id_local INTEGER PRIMARY KEY,
    tag1 NOT NULL DEFAULT '',
    tag2 NOT NULL DEFAULT '',
    value NOT NULL DEFAULT 0
)
CREATE TABLE AgLibraryKeywordFace (
    id_local INTEGER PRIMARY KEY,
    face INTEGER NOT NULL DEFAULT 0,
    keyFace INTEGER,
    rankOrder,
    tag INTEGER NOT NULL DEFAULT 0,
    userPick INTEGER,
    userReject INTEGER
)
CREATE TABLE AgLibraryKeywordImage (
    id_local INTEGER PRIMARY KEY,
    image INTEGER NOT NULL DEFAULT 0,
    tag INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgLibraryKeywordPopularity (
    id_local INTEGER PRIMARY KEY,
    occurrences NOT NULL DEFAULT 0,
    popularity NOT NULL DEFAULT 0,
    tag UNIQUE NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryKeywordSynonym (
    id_local INTEGER PRIMARY KEY,
    keyword INTEGER NOT NULL DEFAULT 0,
    lc_name,
    name
)
CREATE TABLE AgLibraryOzCommentIds(
	ozCatalogId NOT NULL,
	ozSpaceId NOT NULL,
	ozAssetId NOT NULL,
	ozCommentId NOT NULL,
	timestamp NOT NULL
)
CREATE TABLE AgLibraryOzFavoriteIds(
	ozCatalogId NOT NULL,
	ozSpaceId NOT NULL,
	ozAssetId NOT NULL,
	ozFavoriteId NOT NULL,
	timestamp NOT NULL
)
CREATE TABLE AgLibraryOzFeedbackInfo (
    id_local INTEGER PRIMARY KEY,
    image NOT NULL DEFAULT '',
    lastFeedbackTime,
    lastReadTime,
    newCommentCount NOT NULL DEFAULT 0,
    newFavoriteCount NOT NULL DEFAULT 0,
    ozAssetId NOT NULL DEFAULT '',
    ozCatalogId NOT NULL DEFAULT '',
    ozSpaceId NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryPublishedCollection (
    id_local INTEGER PRIMARY KEY,
    creationId NOT NULL DEFAULT '',
    genealogy NOT NULL DEFAULT '',
    imageCount,
    isDefaultCollection,
    name NOT NULL DEFAULT '',
    parent INTEGER,
    publishedUrl,
    remoteCollectionId,
    systemOnly NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryPublishedCollectionContent (
    id_local INTEGER PRIMARY KEY,
    collection INTEGER NOT NULL DEFAULT 0,
    content,
    owningModule
)
CREATE TABLE AgLibraryPublishedCollectionImage (
    id_local INTEGER PRIMARY KEY,
    collection INTEGER NOT NULL DEFAULT 0,
    image INTEGER NOT NULL DEFAULT 0,
    pick NOT NULL DEFAULT 0,
    positionInCollection
)
CREATE TABLE AgLibraryPublishedCollectionLabel (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    collection INTEGER NOT NULL DEFAULT 0,
    label,
    labelData,
    labelGenerics,
    labelType NOT NULL DEFAULT ''
)
CREATE TABLE AgLibraryRootFolder (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    absolutePath UNIQUE NOT NULL DEFAULT '',
    name NOT NULL DEFAULT '',
    relativePathFromCatalog
)
CREATE TABLE AgLibraryUpdatedImages ( image INTEGER PRIMARY KEY )
CREATE TABLE AgMRULists (
    id_local INTEGER PRIMARY KEY,
    listID NOT NULL DEFAULT '',
    timestamp NOT NULL DEFAULT 0,
    value NOT NULL DEFAULT ''
)
CREATE TABLE AgMetadataSearchIndex (
    id_local INTEGER PRIMARY KEY,
    exifSearchIndex NOT NULL DEFAULT '',
    image INTEGER,
    iptcSearchIndex NOT NULL DEFAULT '',
    otherSearchIndex NOT NULL DEFAULT '',
    searchIndex NOT NULL DEFAULT ''
)
CREATE TABLE AgOutputImageAsset (
    id_local INTEGER PRIMARY KEY,
    assetId NOT NULL DEFAULT '',
    collection INTEGER NOT NULL DEFAULT 0,
    image INTEGER NOT NULL DEFAULT 0,
    moduleId NOT NULL DEFAULT ''
)
CREATE TABLE AgOzAssetSettings(
	id_local INTEGER NOT NULL,
	image PRIMARY KEY,
	ozCatalogId NOT NULL,
	sha256 NOT NULL,
	updatedTime NOT NULL
)
CREATE TABLE AgOzAuxBinaryMetadata(
	auxId NOT NULL,
	ozAssetId NOT NULL,
	ozCatalogId NOT NULL,
	digest NOT NULL,
	sha256 NOT NULL,
	fileSize DEFAULT 0,
	type NOT NULL
)
CREATE TABLE AgOzCorruptedAuxIds(
	auxId NOT NULL,
	ozAssetId NOT NULL,
	ozCatalogId NOT NULL
)
CREATE TABLE AgOzDocRevIds(
	localId NOT NULL,
	currRevId NOT NULL,
	docType NOT NULL,
	PRIMARY KEY (localId, docType)
)
CREATE TABLE AgOzSpaceAlbumIds(
	id_local NOT NULL DEFAULT 0,
	ozCatalogId NOT NULL,
	ozAlbumId NOT NULL,
	ozSpaceId NOT NULL,
	ozSpaceAlbumId NOT NULL
)
CREATE TABLE AgOzSpaceIds(
	ozCatalogId NOT NULL,
	ozSpaceId NOT NULL
)
CREATE TABLE AgPendingOzAlbumAssetIds(
	ozCatalogId NOT NULL,
	ozAlbumAssetId NOT NULL,
	ozAssetId NOT NULL,
	ozAlbumId NOT NULL,
	ozSortOrder DEFAULT "",
	ozIsCover DEFAULT 0
)
CREATE TABLE AgPendingOzAssetBinaryDownloads(
	ozAssetId NOT NULL,
	ozCatalogId NOT NULL,
	whenQueued NOT NULL,
	path NOT NULL,
	state DEFAULT "master"
)
CREATE TABLE AgPendingOzAssetDevelopSettings(
	ozAssetId NOT NULL,
	ozCatalogId NOT NULL,
	payloadHash NOT NULL,
	developUserUpdated
)
CREATE TABLE AgPendingOzAssets(
	ozAssetId NOT NULL,
	ozCatalogId NOT NULL,
	state DEFAULT "needs_binary",
	path NOT NULL,
	payload NOT NULL
)
CREATE TABLE AgPendingOzAuxBinaryDownloads(
	auxId NOT NULL,
	ozAssetId NOT NULL,
	ozCatalogId NOT NULL,
	payloadHash NOT NULL,
	whenQueued NOT NULL,
	state NOT NULL
)
CREATE TABLE AgPendingOzDocs(
	id_local INTEGER NOT NULL,
	ozDocId PRIMARY KEY,
	ozCatalogId NOT NULL,
	state DEFAULT "needs_binary",
	fileName NOT NULL,
	path NOT NULL,
	binaryType DEFAULT "original",
	needAux DEFAULT 0,
	needDevelopXmp DEFAULT 0,
	needSidecar DEFAULT 0,
	payload NOT NULL,
	revId DEFAULT 0,
	isLibImage DEFAULT 0,
	isPathChanged DEFAULT 0,
	errorDescription Default ''
)
CREATE TABLE AgPendingOzUploads(
	id_local INTEGER NOT NULL,
	localId,
	ozDocId,
	operation NOT NULL,
	ozCatalogId NOT NULL,
	changeCounter DEFAULT 0
)
CREATE TABLE AgPhotoComment (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    comment,
    commentRealname,
    commentUsername,
    dateCreated,
    photo INTEGER NOT NULL DEFAULT 0,
    remoteId NOT NULL DEFAULT '',
    remotePhoto INTEGER,
    url
)
CREATE TABLE AgPhotoProperty (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    dataType,
    internalValue,
    photo INTEGER NOT NULL DEFAULT 0,
    propertySpec INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgPhotoPropertyArrayElement (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    arrayIndex NOT NULL DEFAULT '',
    dataType,
    internalValue,
    photo INTEGER NOT NULL DEFAULT 0,
    propertySpec INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgPhotoPropertySpec (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    flattenedAttributes,
    key NOT NULL DEFAULT '',
    pluginVersion NOT NULL DEFAULT '',
    sourcePlugin NOT NULL DEFAULT '',
    userVisibleName
)
CREATE TABLE AgPublishListenerWorklist (
    id_local INTEGER PRIMARY KEY,
    taskID UNIQUE NOT NULL DEFAULT '',
    taskStatus NOT NULL DEFAULT 'pending',
    whenPosted NOT NULL DEFAULT ''
)
CREATE TABLE AgRemotePhoto (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    collection INTEGER NOT NULL DEFAULT 0,
    commentCount,
    developSettingsDigest,
    fileContentsHash,
    fileModTimestamp,
    metadataDigest,
    mostRecentCommentTime,
    orientation,
    photo INTEGER NOT NULL DEFAULT 0,
    photoNeedsUpdating DEFAULT 2,
    publishCount,
    remoteId,
    serviceAggregateRating,
    url
)
CREATE TABLE AgSearchablePhotoProperty (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    dataType,
    internalValue,
    lc_idx_internalValue,
    photo INTEGER NOT NULL DEFAULT 0,
    propertySpec INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgSearchablePhotoPropertyArrayElement (
    id_local INTEGER PRIMARY KEY,
    id_global UNIQUE NOT NULL,
    arrayIndex NOT NULL DEFAULT '',
    dataType,
    internalValue,
    lc_idx_internalValue,
    photo INTEGER NOT NULL DEFAULT 0,
    propertySpec INTEGER NOT NULL DEFAULT 0
)
CREATE TABLE AgSourceColorProfileConstants (
    id_local INTEGER PRIMARY KEY,
    image INTEGER NOT NULL DEFAULT 0,
    profileName NOT NULL DEFAULT 'Untagged'
)
CREATE TABLE AgSpecialSourceContent (
    id_local INTEGER PRIMARY KEY,
    content,
    owningModule,
    source NOT NULL DEFAULT ''
)
CREATE TABLE AgTempImages ( image INTEGER PRIMARY KEY )
CREATE TABLE AgUnsupportedOzAssets(
	id_local INTEGER PRIMARY KEY,
	ozAssetId NOT NULL,
	ozCatalogId NOT NULL,
	path NOT NULL,
	type NOT NULL,
	payload NOT NULL
)
CREATE TABLE AgVideoInfo (
    id_local INTEGER PRIMARY KEY,
    duration,
    frame_rate,
    has_audio INTEGER NOT NULL DEFAULT 1,
    has_video INTEGER NOT NULL DEFAULT 1,
    image INTEGER NOT NULL DEFAULT 0,
    poster_frame NOT NULL DEFAULT '0000000000000000/0000000000000001',
    poster_frame_set_by_user INTEGER NOT NULL DEFAULT 0,
    trim_end NOT NULL DEFAULT '0000000000000000/0000000000000001',
    trim_start NOT NULL DEFAULT '0000000000000000/0000000000000001'
)
CREATE TABLE LrMobileSyncChangeCounter(
	id PRIMARY KEY,
	changeCounter NOT NULL
)
CREATE TABLE MigratedCollectionImages(
			ozAlbumId NOT NULL,
			ozAlbumAssetId NOT NULL,
			ozCatalogId NOT NULL,
			localCollectionId INTEGER NOT NULL,
			localCollectionImageId INTEGER NOT NULL,
			UNIQUE ( localCollectionImageId, ozCatalogId )
		)
CREATE TABLE MigratedCollections(
			ozAlbumId NOT NULL,
			ozCatalogId NOT NULL,
			ozName NOT NULL,
			localId INTEGER NOT NULL,
			UNIQUE ( localId, ozCatalogId )
		)
CREATE TABLE MigratedImages(
			ozAssetId NOT NULL,
			ozCatalogId NOT NULL,
			localId INTEGER NOT NULL,
			UNIQUE ( localId, ozCatalogId )
		)
CREATE TABLE MigratedInfo(
			ozCatalogId TEXT PRIMARY KEY,
			migrationStatus NOT NULL,
			timestamp NOT NULL
		)
CREATE TABLE MigrationSchemaVersion(
			version TEXT PRIMARY KEY
		)
CREATE TABLE sqlite_stat1(tbl,idx,stat)
CREATE TABLE sqlite_stat4(tbl,idx,neq,nlt,ndlt,sample)
